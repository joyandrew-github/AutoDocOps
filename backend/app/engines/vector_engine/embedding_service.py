"""EmbeddingService — orchestrates incremental embedding generation."""
import hashlib
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.engines.vector_engine.embedding_providers import BaseEmbeddingProvider, get_embedding_provider
from app.engines.vector_engine.chunker import CodeChunker, Chunk
from app.repositories.vector_repo import VectorRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.parser_repo import ParserRepository
from app.repositories.memory_repo import MemoryRepository
from app.models.parser import ASTNode, Function, Class, Method, Import, Export, Variable, Comment
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    """Generates and manages embeddings for repository code entities."""

    def __init__(self, db: Session, provider: BaseEmbeddingProvider | None = None):
        self.db = db
        self.provider = provider or get_embedding_provider()
        self.chunker = CodeChunker()
        self.vector_repo = VectorRepository(db)
        self.repo_repo = RepositoryRepository(db)
        self.parser_repo = ParserRepository(db)
        self.memory_repo = MemoryRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync_embeddings(self, repository_id: int) -> dict:
        """Full incremental embedding sync for a repository.

        Returns statistics about the sync operation.
        """
        start = time.time()
        stats = {
            "embeddings_created": 0,
            "embeddings_updated": 0,
            "embeddings_deleted": 0,
            "chunks_created": 0,
            "skipped": 0,
            "failed": 0,
            "errors": [],
        }

        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        # Create or get job
        job = self.vector_repo.create_job(repository_id)
        self.vector_repo.update_job(job, status="running", started_at=datetime.now(timezone.utc))

        try:
            # Get existing embedding hashes for incremental comparison
            existing_hashes = self.vector_repo.get_embedding_hashes(repository_id)

            # 1. Handle deletions from memory engine
            deleted = self._handle_deletions(repository_id, stats)

            # 2. Process all current entities
            self._process_entities(repository_id, existing_hashes, stats)

            # 3. Update search index
            idx = self.vector_repo.get_or_create_search_index(repository_id)
            snapshot = self.memory_repo.get_latest_snapshot(repository_id)
            self.vector_repo.update_search_index(idx,
                total_embeddings=self.vector_repo.count_embeddings(repository_id),
                total_chunks=self.vector_repo.count_chunks(repository_id),
                last_synced_at=datetime.now(timezone.utc),
                last_snapshot_id=snapshot.id if snapshot else None,
                index_status="ready",
                dimension=self.provider.dimension,
                provider=self.provider.name,
            )

            duration = round(time.time() - start, 3)
            stats["duration_seconds"] = duration

            self.vector_repo.update_job(job,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_entities=stats["embeddings_created"] + stats["embeddings_updated"] + stats["skipped"],
                processed_entities=stats["embeddings_created"] + stats["embeddings_updated"],
                failed_entities=stats["failed"],
                skipped_entities=stats["skipped"],
                embeddings_created=stats["embeddings_created"],
                embeddings_updated=stats["embeddings_updated"],
                embeddings_deleted=stats["embeddings_deleted"],
                duration_seconds=duration,
            )

            logger.info(
                f"Embedding sync completed for repository {repository_id} in {duration}s: "
                f"+{stats['embeddings_created']} created, ~{stats['embeddings_updated']} updated, "
                f"-{stats['embeddings_deleted']} deleted, {stats['chunks_created']} chunks, "
                f"{stats['skipped']} skipped, {stats['failed']} failed"
            )

        except Exception as e:
            logger.error(f"Embedding sync failed for repository {repository_id}: {e}")
            self.vector_repo.update_job(job,
                status="failed",
                error_message=str(e),
                retry_count=job.retry_count + 1,
                completed_at=datetime.now(timezone.utc),
            )
            stats["errors"].append(str(e))

        return stats

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _handle_deletions(self, repository_id: int, stats: dict) -> int:
        """Remove embeddings for deleted entities using Memory Engine change sets."""
        deleted_count = 0
        try:
            latest_snapshot = self.memory_repo.get_latest_snapshot(repository_id)
            if not latest_snapshot:
                return 0

            change_sets = self.memory_repo.get_change_sets_by_repository(repository_id, limit=1)
            if not change_sets:
                return 0

            cs = change_sets[0]
            if cs.snapshot_id != latest_snapshot.id:
                return 0

            # Delete embeddings for deleted files
            file_changes = self.memory_repo.get_file_changes_by_change_set(cs.id)
            for fc in file_changes:
                if fc.change_type == "deleted":
                    try:
                        count = self.vector_repo.delete_embeddings_by_file_path(repository_id, fc.file_path)
                        deleted_count += count
                        stats["embeddings_deleted"] += count
                    except Exception as e:
                        logger.error(f"Failed to delete embeddings for file {fc.file_path}: {e}")
                        stats["errors"].append(f"delete file embeddings {fc.file_path}: {e}")

            # Delete embeddings for deleted entities
            entity_changes = self.memory_repo.get_entity_changes_by_change_set(cs.id)
            for ec in entity_changes:
                if ec.change_type == "deleted":
                    try:
                        count = self.vector_repo.delete_embeddings_by_entity(
                            repository_id, ec.entity_type, ec.entity_name, ec.file_path
                        )
                        deleted_count += count
                        stats["embeddings_deleted"] += count
                    except Exception as e:
                        logger.error(f"Failed to delete embedding for entity {ec.entity_name}: {e}")
                        stats["errors"].append(f"delete entity embedding {ec.entity_name}: {e}")

        except Exception as e:
            logger.error(f"Failed to handle deletions: {e}")
            stats["errors"].append(f"deletions: {e}")

        return deleted_count

    def _process_entities(self, repository_id: int, existing_hashes: dict[str, int], stats: dict) -> None:
        """Process all parsed entities and generate embeddings."""
        files = self.repo_repo.get_files_by_repository(repository_id)
        file_map = {f.id: f for f in files}

        nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)
        if not nodes:
            return

        # Batch texts for embedding
        batch_items: list[dict] = []

        for node in nodes:
            rf = file_map.get(node.file_id)
            if not rf:
                continue

            try:
                text, entity_type = self._build_entity_text(node, rf)
                if not text:
                    continue

                content_hash = hashlib.sha256(text.encode()).hexdigest()

                # Skip if unchanged
                if content_hash in existing_hashes:
                    stats["skipped"] += 1
                    continue

                batch_items.append({
                    "node": node,
                    "file": rf,
                    "text": text,
                    "entity_type": entity_type,
                    "content_hash": content_hash,
                })

            except Exception as e:
                logger.error(f"Failed to prepare entity {node.id}: {e}")
                stats["errors"].append(f"prepare {node.id}: {e}")
                stats["failed"] += 1

        # Process in batches
        batch_size = settings.EMBEDDING_BATCH_SIZE
        for i in range(0, len(batch_items), batch_size):
            batch = batch_items[i:i + batch_size]
            self._process_batch(repository_id, batch, stats)

    def _process_batch(self, repository_id: int, batch: list[dict], stats: dict) -> None:
        """Process a batch of entities — generate embeddings and store."""
        if not batch:
            return

        texts = [item["text"] for item in batch]
        try:
            vectors = self.provider.embed_batch(texts)
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            stats["errors"].append(f"batch embed: {e}")
            stats["failed"] += len(batch)
            return

        for item, vector in zip(batch, vectors):
            try:
                node = item["node"]
                rf = item["file"]
                text = item["text"]

                # Check if we should update existing
                existing = self.vector_repo.get_embedding_by_content_hash(repository_id, item["content_hash"])
                if existing:
                    stats["skipped"] += 1
                    continue

                # Delete old embeddings for this entity (for updates)
                self.vector_repo.delete_embeddings_by_entity(
                    repository_id, item["entity_type"], node.name or "", rf.relative_path
                )

                # Create embedding record
                emb = self.vector_repo.create_embedding(
                    repository_id=repository_id,
                    entity_type=item["entity_type"],
                    entity_id=node.id,
                    entity_name=node.name or "",
                    file_path=rf.relative_path,
                    content_hash=item["content_hash"],
                    embedding_text=text[:2000],
                    token_count=self.provider.count_tokens(text),
                    language=rf.language,
                    provider=self.provider.name,
                    model=self.provider.model_name,
                    dimension=self.provider.dimension,
                )
                stats["embeddings_created"] += 1

                # Create chunks
                chunks = self.chunker.chunk_text(text, start_line=node.start_line)
                for chunk in chunks:
                    self.vector_repo.create_chunk(
                        embedding_id=emb.id,
                        repository_id=repository_id,
                        chunk_index=chunk.chunk_index,
                        text=chunk.text,
                        token_count=chunk.token_count,
                        entity_type=item["entity_type"],
                        entity_name=node.name or "",
                        file_path=rf.relative_path,
                        language=rf.language,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        content_hash=chunk.content_hash,
                    )
                    stats["chunks_created"] += 1

            except Exception as e:
                logger.error(f"Failed to store embedding for {item.get('entity_type')} {node.name}: {e}")
                stats["errors"].append(f"store {node.name}: {e}")
                stats["failed"] += 1

    def _build_entity_text(self, node: ASTNode, rf) -> tuple[str, str]:
        """Build embedding text for a parsed entity. Returns (text, entity_type)."""
        entity_type = node.node_type
        content = ""
        docstring = None
        signature = None

        if isinstance(node, Function):
            signature = f"def {node.name}({node.parameters or ''})"
            if node.return_type:
                signature += f" -> {node.return_type}"
            docstring = node.docstring
            content = signature

        elif isinstance(node, Class):
            signature = f"class {node.name}"
            if node.bases:
                signature += f"({node.bases})"
            docstring = node.docstring
            content = signature

        elif isinstance(node, Method):
            signature = f"def {node.name}({node.parameters or ''})"
            if node.return_type:
                signature += f" -> {node.return_type}"
            if node.class_name:
                content = f"{node.class_name}.{signature}"
            else:
                content = signature

        elif isinstance(node, Import):
            content = f"import {node.module or ''}"
            if node.name:
                content += f" ({node.name})"

        elif isinstance(node, Export):
            content = f"export {node.name or ''}"

        elif isinstance(node, Variable):
            content = f"{node.name}: {node.var_type or 'unknown'}"
            if node.is_constant:
                content = f"const {content}"

        elif isinstance(node, Comment):
            content = getattr(node, "text", "") or ""
            entity_type = "comment"

        else:
            content = node.name or ""

        if not content:
            return "", entity_type

        text = self.chunker.build_embedding_text(
            entity_type=entity_type,
            entity_name=node.name or "",
            content=content,
            file_path=rf.relative_path,
            language=rf.language,
            docstring=docstring,
            signature=signature,
        )
        return text, entity_type

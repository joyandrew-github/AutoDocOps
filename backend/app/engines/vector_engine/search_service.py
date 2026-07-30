"""SimilaritySearchService — semantic similarity search over code embeddings."""
import math
from sqlalchemy.orm import Session
from app.engines.vector_engine.embedding_providers import BaseEmbeddingProvider, get_embedding_provider
from app.repositories.vector_repo import VectorRepository
from app.models.vector import Embedding, CodeChunk
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimilaritySearchService:
    """Provides semantic similarity search over code embeddings using cosine similarity."""

    def __init__(self, db: Session, provider: BaseEmbeddingProvider | None = None):
        self.db = db
        self.provider = provider or get_embedding_provider()
        self.vector_repo = VectorRepository(db)

    def search(
        self,
        query: str,
        repository_id: int | None = None,
        entity_type: str | None = None,
        language: str | None = None,
        top_k: int = 10,
    ) -> list[dict]:
        """Perform semantic similarity search.

        Args:
            query: Natural language search query.
            repository_id: Filter to a specific repository.
            entity_type: Filter by entity type (class, function, method, etc.).
            language: Filter by programming language.
            top_k: Number of results to return.

        Returns:
            List of search results with similarity scores.
        """
        if not query or not query.strip():
            return []

        try:
            query_vector = self.provider.embed_text(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []

        # Get candidate embeddings with filters
        candidates = self._get_candidates(repository_id, entity_type, language)

        if not candidates:
            return []

        # Compute cosine similarity and rank
        results = []
        for emb in candidates:
            try:
                # Use the embedding text to generate the candidate vector for comparison
                candidate_vector = self.provider.embed_text(emb.embedding_text or emb.entity_name)
                score = self._cosine_similarity(query_vector, candidate_vector)
                results.append({
                    "embedding_id": emb.id,
                    "entity_type": emb.entity_type,
                    "entity_name": emb.entity_name,
                    "file_path": emb.file_path,
                    "language": emb.language,
                    "repository_id": emb.repository_id,
                    "similarity": round(score, 4),
                    "token_count": emb.token_count,
                    "preview": (emb.embedding_text or "")[:200],
                })
            except Exception as e:
                logger.error(f"Failed to compute similarity for embedding {emb.id}: {e}")
                continue

        # Sort by similarity descending
        results.sort(key=lambda r: r["similarity"], reverse=True)
        return results[:top_k]

    def search_similar_entity(
        self,
        repository_id: int,
        entity_type: str,
        entity_name: str,
        top_k: int = 10,
    ) -> list[dict]:
        """Find entities similar to a given entity."""
        # Find the source embedding
        embeddings = self.vector_repo.get_embeddings_by_repository(repository_id, entity_type)
        source = None
        for emb in embeddings:
            if emb.entity_name == entity_name:
                source = emb
                break

        if not source:
            return []

        source_text = source.embedding_text or source.entity_name
        return self.search(
            query=source_text,
            repository_id=repository_id,
            entity_type=entity_type,
            top_k=top_k + 1,  # +1 to exclude the source itself
        )[:top_k]

    def search_by_file(self, repository_id: int, file_id: int, top_k: int = 10) -> list[dict]:
        """Get embeddings related to a specific file."""
        from app.repositories.repository_repo import RepositoryRepository
        repo_repo = RepositoryRepository(self.db)
        files = repo_repo.get_files_by_repository(repository_id)
        target_file = None
        for f in files:
            if f.id == file_id:
                target_file = f
                break

        if not target_file:
            return []

        embeddings = self.vector_repo.get_embeddings_by_repository(repository_id)
        results = []
        for emb in embeddings:
            if emb.file_path == target_file.relative_path:
                results.append({
                    "embedding_id": emb.id,
                    "entity_type": emb.entity_type,
                    "entity_name": emb.entity_name,
                    "file_path": emb.file_path,
                    "language": emb.language,
                    "repository_id": emb.repository_id,
                    "similarity": 1.0,
                    "token_count": emb.token_count,
                    "preview": (emb.embedding_text or "")[:200],
                })

        return results[:top_k]

    def search_by_function(self, repository_id: int, function_id: int, top_k: int = 10) -> list[dict]:
        """Get embeddings for a specific function and find similar ones."""
        embeddings = self.vector_repo.get_embeddings_by_entity(repository_id, "function", function_id)
        if not embeddings:
            # Also check methods
            embeddings = self.vector_repo.get_embeddings_by_entity(repository_id, "method", function_id)

        if not embeddings:
            return []

        source = embeddings[0]
        return self.search(
            query=source.embedding_text or source.entity_name,
            repository_id=repository_id,
            top_k=top_k,
        )

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _get_candidates(
        self,
        repository_id: int | None,
        entity_type: str | None,
        language: str | None,
    ) -> list[Embedding]:
        """Get candidate embeddings with optional filters."""
        q = self.db.query(Embedding)
        if repository_id:
            q = q.filter(Embedding.repository_id == repository_id)
        if entity_type:
            q = q.filter(Embedding.entity_type == entity_type)
        if language:
            q = q.filter(Embedding.language == language)
        return q.limit(1000).all()

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot / (norm_a * norm_b)

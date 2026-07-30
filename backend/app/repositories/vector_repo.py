"""Data access layer for Vector Search & Semantic Retrieval Engine."""
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func as sa_func, text
from app.models.vector import Embedding, CodeChunk, SearchIndex, EmbeddingJob


class VectorRepository:
    """Data access layer for vector search entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- Embedding ---

    def create_embedding(self, **kwargs) -> Embedding:
        emb = Embedding(**kwargs)
        self.db.add(emb)
        self.db.commit()
        self.db.refresh(emb)
        return emb

    def bulk_create_embeddings(self, records: list[dict]) -> list[Embedding]:
        embeddings = []
        for rec in records:
            emb = Embedding(**rec)
            self.db.add(emb)
            embeddings.append(emb)
        self.db.commit()
        for emb in embeddings:
            self.db.refresh(emb)
        return embeddings

    def get_embedding_by_id(self, embedding_id: int) -> Embedding | None:
        return self.db.query(Embedding).filter(Embedding.id == embedding_id).first()

    def get_embedding_by_content_hash(self, repository_id: int, content_hash: str) -> Embedding | None:
        return (
            self.db.query(Embedding)
            .filter(Embedding.repository_id == repository_id, Embedding.content_hash == content_hash)
            .first()
        )

    def get_embeddings_by_repository(self, repository_id: int, entity_type: str | None = None) -> list[Embedding]:
        q = self.db.query(Embedding).filter(Embedding.repository_id == repository_id)
        if entity_type:
            q = q.filter(Embedding.entity_type == entity_type)
        return q.order_by(Embedding.entity_type, Embedding.entity_name).all()

    def get_embeddings_by_entity(self, repository_id: int, entity_type: str, entity_id: int) -> list[Embedding]:
        return (
            self.db.query(Embedding)
            .filter(
                Embedding.repository_id == repository_id,
                Embedding.entity_type == entity_type,
                Embedding.entity_id == entity_id,
            )
            .all()
        )

    def get_embedding_hashes(self, repository_id: int) -> dict[str, int]:
        """Get mapping of content_hash -> embedding_id for a repository."""
        rows = (
            self.db.query(Embedding.content_hash, Embedding.id)
            .filter(Embedding.repository_id == repository_id, Embedding.content_hash.isnot(None))
            .all()
        )
        return {row[0]: row[1] for row in rows}

    def delete_embedding(self, embedding_id: int) -> None:
        self.db.query(Embedding).filter(Embedding.id == embedding_id).delete()
        self.db.commit()

    def delete_embeddings_by_repository(self, repository_id: int) -> int:
        count = self.db.query(Embedding).filter(Embedding.repository_id == repository_id).delete()
        self.db.commit()
        return count

    def delete_embeddings_by_file_path(self, repository_id: int, file_path: str) -> int:
        count = (
            self.db.query(Embedding)
            .filter(Embedding.repository_id == repository_id, Embedding.file_path == file_path)
            .delete()
        )
        self.db.commit()
        return count

    def delete_embeddings_by_entity(self, repository_id: int, entity_type: str, entity_name: str, file_path: str) -> int:
        count = (
            self.db.query(Embedding)
            .filter(
                Embedding.repository_id == repository_id,
                Embedding.entity_type == entity_type,
                Embedding.entity_name == entity_name,
                Embedding.file_path == file_path,
            )
            .delete()
        )
        self.db.commit()
        return count

    def count_embeddings(self, repository_id: int) -> int:
        return self.db.query(Embedding).filter(Embedding.repository_id == repository_id).count()

    # --- CodeChunk ---

    def create_chunk(self, **kwargs) -> CodeChunk:
        chunk = CodeChunk(**kwargs)
        self.db.add(chunk)
        self.db.commit()
        self.db.refresh(chunk)
        return chunk

    def bulk_create_chunks(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(CodeChunk(**rec))
        self.db.commit()

    def get_chunks_by_embedding(self, embedding_id: int) -> list[CodeChunk]:
        return (
            self.db.query(CodeChunk)
            .filter(CodeChunk.embedding_id == embedding_id)
            .order_by(CodeChunk.chunk_index)
            .all()
        )

    def get_chunks_by_repository(
        self,
        repository_id: int,
        entity_type: str | None = None,
        language: str | None = None,
        limit: int = 100,
    ) -> list[CodeChunk]:
        q = self.db.query(CodeChunk).filter(CodeChunk.repository_id == repository_id)
        if entity_type:
            q = q.filter(CodeChunk.entity_type == entity_type)
        if language:
            q = q.filter(CodeChunk.language == language)
        return q.order_by(CodeChunk.id).limit(limit).all()

    def count_chunks(self, repository_id: int) -> int:
        return self.db.query(CodeChunk).filter(CodeChunk.repository_id == repository_id).count()

    def delete_chunks_by_embedding(self, embedding_id: int) -> None:
        self.db.query(CodeChunk).filter(CodeChunk.embedding_id == embedding_id).delete()
        self.db.commit()

    # --- SearchIndex ---

    def get_or_create_search_index(self, repository_id: int) -> SearchIndex:
        idx = (
            self.db.query(SearchIndex)
            .filter(SearchIndex.repository_id == repository_id)
            .first()
        )
        if not idx:
            idx = SearchIndex(repository_id=repository_id)
            self.db.add(idx)
            self.db.commit()
            self.db.refresh(idx)
        return idx

    def update_search_index(self, idx: SearchIndex, **kwargs) -> SearchIndex:
        for key, value in kwargs.items():
            if hasattr(idx, key):
                setattr(idx, key, value)
        self.db.commit()
        self.db.refresh(idx)
        return idx

    # --- EmbeddingJob ---

    def create_job(self, repository_id: int) -> EmbeddingJob:
        job = EmbeddingJob(repository_id=repository_id)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job(self, job: EmbeddingJob, **kwargs) -> EmbeddingJob:
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_pending_jobs(self, repository_id: int) -> list[EmbeddingJob]:
        return (
            self.db.query(EmbeddingJob)
            .filter(
                EmbeddingJob.repository_id == repository_id,
                EmbeddingJob.status.in_(["pending", "failed"]),
            )
            .filter(EmbeddingJob.retry_count < EmbeddingJob.max_retries)
            .order_by(EmbeddingJob.created_at)
            .all()
        )

    def get_latest_job(self, repository_id: int) -> EmbeddingJob | None:
        return (
            self.db.query(EmbeddingJob)
            .filter(EmbeddingJob.repository_id == repository_id)
            .order_by(desc(EmbeddingJob.created_at))
            .first()
        )

    def get_jobs_by_repository(self, repository_id: int, limit: int = 20) -> list[EmbeddingJob]:
        return (
            self.db.query(EmbeddingJob)
            .filter(EmbeddingJob.repository_id == repository_id)
            .order_by(desc(EmbeddingJob.created_at))
            .limit(limit)
            .all()
        )

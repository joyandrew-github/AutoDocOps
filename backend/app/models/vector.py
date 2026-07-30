"""Models for the Vector Search & Semantic Retrieval Engine."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, BigInteger, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Embedding(Base, TimestampMixin):
    """Model storing vector embeddings for code entities."""

    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, index=True)
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    embedding_text: Mapped[str | None] = mapped_column(Text)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    language: Mapped[str | None] = mapped_column(String(100), index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")
    model: Mapped[str | None] = mapped_column(String(100))
    dimension: Mapped[int] = mapped_column(Integer, default=1536)

    chunks: Mapped[list["CodeChunk"]] = relationship(
        "CodeChunk", back_populates="embedding", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Embedding(id={self.id}, entity={self.entity_type}:{self.entity_name})>"


class CodeChunk(Base, TimestampMixin):
    """Model storing chunked code segments with their embeddings."""

    __tablename__ = "code_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    embedding_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("embeddings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    language: Mapped[str | None] = mapped_column(String(100), index=True)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(64))

    embedding: Mapped["Embedding"] = relationship("Embedding", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<CodeChunk(id={self.id}, embedding_id={self.embedding_id}, chunk={self.chunk_index})>"


class SearchIndex(Base, TimestampMixin):
    """Model tracking search index status per repository."""

    __tablename__ = "search_indexes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True, unique=True
    )
    total_embeddings: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_snapshot_id: Mapped[int | None] = mapped_column(Integer)
    index_status: Mapped[str] = mapped_column(String(50), default="pending")
    dimension: Mapped[int] = mapped_column(Integer, default=1536)
    provider: Mapped[str] = mapped_column(String(50), default="mock")

    def __repr__(self) -> str:
        return f"<SearchIndex(id={self.id}, repo_id={self.repository_id}, status={self.index_status})>"


class EmbeddingJob(Base, TimestampMixin):
    """Model tracking embedding generation jobs."""

    __tablename__ = "embedding_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    total_entities: Mapped[int] = mapped_column(Integer, default=0)
    processed_entities: Mapped[int] = mapped_column(Integer, default=0)
    failed_entities: Mapped[int] = mapped_column(Integer, default=0)
    skipped_entities: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_created: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_updated: Mapped[int] = mapped_column(Integer, default=0)
    embeddings_deleted: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<EmbeddingJob(id={self.id}, repo_id={self.repository_id}, status={self.status})>"

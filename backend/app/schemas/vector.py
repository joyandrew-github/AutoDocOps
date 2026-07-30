"""Pydantic schemas for the Vector Search & Semantic Retrieval Engine."""
from datetime import datetime
from pydantic import BaseModel


class EmbeddingSyncResponse(BaseModel):
    repository_id: int
    embeddings_created: int = 0
    embeddings_updated: int = 0
    embeddings_deleted: int = 0
    chunks_created: int = 0
    skipped: int = 0
    failed: int = 0
    duration_seconds: float | None = None
    errors: list[str] = []


class SearchRequest(BaseModel):
    query: str
    repository_id: int | None = None
    entity_type: str | None = None
    language: str | None = None
    top_k: int = 10


class SearchResult(BaseModel):
    embedding_id: int
    entity_type: str
    entity_name: str
    file_path: str | None = None
    language: str | None = None
    repository_id: int
    similarity: float
    token_count: int = 0
    preview: str = ""


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult] = []
    total: int = 0


class EmbeddingDetail(BaseModel):
    id: int
    repository_id: int
    entity_type: str
    entity_name: str
    file_path: str | None = None
    content_hash: str | None = None
    token_count: int = 0
    language: str | None = None
    provider: str = ""
    model: str | None = None
    dimension: int = 0
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ChunkDetail(BaseModel):
    id: int
    embedding_id: int
    chunk_index: int
    text: str
    token_count: int = 0
    entity_type: str
    entity_name: str
    file_path: str | None = None
    language: str | None = None
    start_line: int | None = None
    end_line: int | None = None

    class Config:
        from_attributes = True


class SearchIndexDetail(BaseModel):
    repository_id: int
    total_embeddings: int = 0
    total_chunks: int = 0
    last_synced_at: datetime | None = None
    last_snapshot_id: int | None = None
    index_status: str = "pending"
    dimension: int = 0
    provider: str = ""

    class Config:
        from_attributes = True


class EmbeddingJobDetail(BaseModel):
    id: int
    repository_id: int
    status: str
    total_entities: int = 0
    processed_entities: int = 0
    failed_entities: int = 0
    skipped_entities: int = 0
    embeddings_created: int = 0
    embeddings_updated: int = 0
    embeddings_deleted: int = 0
    duration_seconds: float | None = None
    error_message: str | None = None
    retry_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True

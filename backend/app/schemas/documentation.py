"""Pydantic schemas for the Intelligent Documentation Engine."""
from datetime import datetime
from pydantic import BaseModel


class DocumentationGenerateRequest(BaseModel):
    doc_types: list[str] | None = None


class DocumentationGenerateResponse(BaseModel):
    repository_id: int
    documents_created: int = 0
    documents_updated: int = 0
    documents_skipped: int = 0
    documents_failed: int = 0
    duration_seconds: float | None = None
    errors: list[str] = []


class DocumentationSectionDetail(BaseModel):
    id: int
    title: str
    content: str | None = None
    section_order: int = 0
    section_type: str = "content"
    level: int = 2

    class Config:
        from_attributes = True


class DocumentationDetail(BaseModel):
    id: int
    repository_id: int
    doc_type: str
    title: str
    slug: str
    entity_type: str | None = None
    entity_name: str | None = None
    file_path: str | None = None
    content: str | None = None
    summary: str | None = None
    format: str = "markdown"
    is_published: bool = True
    version: int = 1
    language: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    sections: list[DocumentationSectionDetail] = []

    class Config:
        from_attributes = True


class DocumentationListItem(BaseModel):
    id: int
    doc_type: str
    title: str
    slug: str
    entity_type: str | None = None
    entity_name: str | None = None
    file_path: str | None = None
    summary: str | None = None
    version: int = 1
    language: str | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class DocumentationSearchRequest(BaseModel):
    query: str
    repository_id: int
    limit: int = 20


class DocumentationExportRequest(BaseModel):
    doc_id: int | None = None
    repository_id: int | None = None
    format: str = "markdown"


class DocumentationExportResponse(BaseModel):
    title: str
    doc_type: str
    content: str
    format: str


class DocumentationJobDetail(BaseModel):
    id: int
    repository_id: int
    status: str
    total_documents: int = 0
    documents_created: int = 0
    documents_updated: int = 0
    documents_skipped: int = 0
    documents_failed: int = 0
    duration_seconds: float | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True

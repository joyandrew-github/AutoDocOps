"""Pydantic schemas for the Architecture Intelligence Engine."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class ArchitectureGenerateResponse(BaseModel):
    repository_id: int
    models_created: int = 0
    models_updated: int = 0
    models_skipped: int = 0
    diagrams_generated: int = 0
    violations_detected: int = 0
    duration_seconds: float | None = None
    errors: list[str] = []


class ArchitectureDiagramDetail(BaseModel):
    id: int
    diagram_type: str
    title: str
    format: str
    content: str | None = None
    content_hash: str | None = None

    class Config:
        from_attributes = True


class ArchitectureModelDetail(BaseModel):
    id: int
    repository_id: int
    model_type: str
    name: str
    description: str | None = None
    data: Any | None = None
    content_hash: str | None = None
    version: int = 1
    created_at: datetime | None = None
    updated_at: datetime | None = None
    diagrams: list[ArchitectureDiagramDetail] = []

    class Config:
        from_attributes = True


class ArchitectureModelListItem(BaseModel):
    id: int
    model_type: str
    name: str
    description: str | None = None
    version: int = 1
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ArchitectureViolationDetail(BaseModel):
    id: int
    repository_id: int
    violation_type: str
    severity: str
    description: str
    source_entity: str | None = None
    target_entity: str | None = None
    source_file: str | None = None
    target_file: str | None = None
    source_layer: str | None = None
    target_layer: str | None = None
    is_resolved: bool = False
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class DependencyGraphResponse(BaseModel):
    file_dependencies: dict[str, list[str]] = {}
    module_dependencies: dict[str, list[str]] = {}
    total_imports: int = 0


class CallGraphResponse(BaseModel):
    nodes: list[dict] = []
    edges: list[dict] = []
    node_count: int = 0
    edge_count: int = 0


class ArchitectureSnapshotDetail(BaseModel):
    id: int
    repository_id: int
    status: str
    total_models: int = 0
    models_created: int = 0
    models_updated: int = 0
    models_skipped: int = 0
    diagrams_generated: int = 0
    violations_detected: int = 0
    duration_seconds: float | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True

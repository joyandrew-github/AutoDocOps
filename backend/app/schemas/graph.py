from pydantic import BaseModel


class GraphSyncResponse(BaseModel):
    repository_id: int
    nodes_created: int = 0
    nodes_updated: int = 0
    nodes_deleted: int = 0
    relationships_created: int = 0
    relationships_removed: int = 0
    duration_seconds: float | None = None
    errors: list[str] = []


class GraphStatisticsResponse(BaseModel):
    repository_id: int
    total_nodes: int = 0
    total_relationships: int = 0
    node_counts: dict[str, int] = {}


class GraphNodeResponse(BaseModel):
    element_id: str
    labels: list[str] = []
    properties: dict = {}


class GraphNeighborResponse(BaseModel):
    element_id: str
    labels: list[str] = []
    relationship_type: str
    properties: dict = {}


class ConnectedFileResponse(BaseModel):
    path: str
    language: str | None = None
    connections: int = 0


class LargestClassResponse(BaseModel):
    name: str
    file_path: str | None = None
    method_count: int = 0


class DependencyEdgeResponse(BaseModel):
    file_path: str
    dependency: str
    version: str | None = None


class ImportEdgeResponse(BaseModel):
    file_path: str
    module: str | None = None
    name: str | None = None


class CallEdgeResponse(BaseModel):
    caller: str
    caller_type: str
    callee: str
    callee_type: str


class LanguageStatResponse(BaseModel):
    language: str
    file_count: int = 0


class FrameworkStatResponse(BaseModel):
    name: str
    version: str | None = None
    confidence: str | None = None

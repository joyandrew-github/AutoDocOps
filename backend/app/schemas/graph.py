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


class LabelCount(BaseModel):
    label: str
    count: int


class RelationshipTypeCount(BaseModel):
    type: str
    count: int


class GraphStatisticsResponse(BaseModel):
    repository_id: int
    total_nodes: int = 0
    total_relationships: int = 0
    node_counts: dict[str, int] = {}
    node_labels: list[LabelCount] = []
    relationship_counts: dict[str, int] = {}
    relationship_types: list[RelationshipTypeCount] = []


class GraphVisualizationNode(BaseModel):
    id: str
    element_id: str | None = None
    label: str
    labels: list[str] = []
    name: str
    properties: dict = {}


class GraphVisualizationEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: dict = {}


class GraphSubgraphResponse(BaseModel):
    repository_id: int
    nodes: list[GraphVisualizationNode] = []
    edges: list[GraphVisualizationEdge] = []
    total_nodes: int = 0
    total_edges: int = 0


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

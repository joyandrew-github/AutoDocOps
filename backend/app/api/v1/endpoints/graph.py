from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.neo4j import get_neo4j_client, Neo4jClient
from app.engines.graph_engine.graph_sync_service import GraphSyncService
from app.engines.graph_engine.graph_query_service import GraphQueryService
from app.schemas.graph import (
    GraphSyncResponse,
    GraphStatisticsResponse,
    GraphNodeResponse,
    GraphNeighborResponse,
    ConnectedFileResponse,
    LargestClassResponse,
    DependencyEdgeResponse,
    ImportEdgeResponse,
    CallEdgeResponse,
    LanguageStatResponse,
    FrameworkStatResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_sync_service(
    db: Session = Depends(get_db),
    neo4j: Neo4jClient = Depends(get_neo4j_client),
) -> GraphSyncService:
    return GraphSyncService(db, neo4j)


def _get_query_service(
    neo4j: Neo4jClient = Depends(get_neo4j_client),
) -> GraphQueryService:
    return GraphQueryService(neo4j)


@router.post(
    "/repositories/{repository_id}/graph/sync",
    response_model=GraphSyncResponse,
    summary="Sync repository to Neo4j graph",
    description="Synchronize PostgreSQL parsed entities into the Neo4j knowledge graph.",
)
def sync_graph(
    repository_id: int,
    sync_service: GraphSyncService = Depends(_get_sync_service),
):
    try:
        stats = sync_service.sync_repository(repository_id)
        return GraphSyncResponse(repository_id=repository_id, **stats)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Graph sync failed for repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during graph synchronization.",
        )


@router.get(
    "/repositories/{repository_id}/graph/statistics",
    response_model=GraphStatisticsResponse,
    summary="Get graph statistics",
    description="Get node and relationship counts for a repository's knowledge graph.",
)
def get_statistics(
    repository_id: int,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.get_statistics(repository_id)


@router.get(
    "/repositories/{repository_id}/graph/node/{element_id}",
    response_model=GraphNodeResponse,
    summary="Get a graph node",
    description="Retrieve a specific node from the knowledge graph by its element ID.",
)
def get_node(
    repository_id: int,
    element_id: str,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    node = query_service.get_node(element_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node not found: {element_id}",
        )
    return node


@router.get(
    "/repositories/{repository_id}/graph/neighbors/{element_id}",
    response_model=list[GraphNeighborResponse],
    summary="Get neighbors of a graph node",
    description="Retrieve neighboring nodes connected to the specified node.",
)
def get_neighbors(
    repository_id: int,
    element_id: str,
    direction: str = "both",
    limit: int = 50,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.get_neighbors(element_id, direction, limit)


# --- Analytics endpoints ---

@router.get(
    "/repositories/{repository_id}/graph/analytics/connected-files",
    response_model=list[ConnectedFileResponse],
    summary="Most connected files",
    description="Files with the most relationships in the knowledge graph.",
)
def most_connected_files(
    repository_id: int,
    limit: int = 10,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.most_connected_files(repository_id, limit)


@router.get(
    "/repositories/{repository_id}/graph/analytics/largest-classes",
    response_model=list[LargestClassResponse],
    summary="Largest classes",
    description="Classes with the most methods.",
)
def largest_classes(
    repository_id: int,
    limit: int = 10,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.largest_classes(repository_id, limit)


@router.get(
    "/repositories/{repository_id}/graph/analytics/dependency-graph",
    response_model=list[DependencyEdgeResponse],
    summary="Dependency graph",
    description="File-to-dependency relationships.",
)
def dependency_graph(
    repository_id: int,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.dependency_graph(repository_id)


@router.get(
    "/repositories/{repository_id}/graph/analytics/import-graph",
    response_model=list[ImportEdgeResponse],
    summary="Import graph",
    description="File-to-import relationships.",
)
def import_graph(
    repository_id: int,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.import_graph(repository_id)


@router.get(
    "/repositories/{repository_id}/graph/analytics/call-graph",
    response_model=list[CallEdgeResponse],
    summary="Call graph",
    description="Function/method call relationships.",
)
def call_graph(
    repository_id: int,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.call_graph(repository_id)


@router.get(
    "/repositories/{repository_id}/graph/analytics/languages",
    response_model=list[LanguageStatResponse],
    summary="Language statistics",
    description="Language distribution in the knowledge graph.",
)
def language_statistics(
    repository_id: int,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.language_statistics(repository_id)


@router.get(
    "/repositories/{repository_id}/graph/analytics/frameworks",
    response_model=list[FrameworkStatResponse],
    summary="Framework statistics",
    description="Detected frameworks in the knowledge graph.",
)
def framework_statistics(
    repository_id: int,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.framework_statistics(repository_id)

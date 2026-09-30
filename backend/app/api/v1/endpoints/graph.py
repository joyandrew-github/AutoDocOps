from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.neo4j import get_neo4j_client, Neo4jClient
from app.engines.graph_engine.graph_sync_service import GraphSyncService
from app.engines.graph_engine.graph_query_service import GraphQueryService
from app.schemas.graph import (
    GraphSyncResponse,
    GraphStatisticsResponse,
    GraphSubgraphResponse,
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


@router.get(
    "/graph/stats",
    response_model=GraphStatisticsResponse,
    summary="Get global graph statistics",
    description="Get node and relationship counts across all repositories in Neo4j.",
)
def get_global_statistics(
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.get_global_statistics()


@router.get(
    "/repositories/{repository_id}/graph/subgraph",
    response_model=GraphSubgraphResponse,
    summary="Get visual graph subgraph",
    description="Retrieve nodes and relationships for visual graph rendering.",
)
def get_subgraph(
    repository_id: int,
    limit: int = 70,
    filter_label: str | None = None,
    query_service: GraphQueryService = Depends(_get_query_service),
):
    return query_service.get_subgraph(repository_id, limit, filter_label)


@router.post(
    "/repositories/{repository_id}/graph/sync",
    response_model=GraphSyncResponse,
    summary="Sync repository to Neo4j graph",
    description="Synchronize PostgreSQL parsed entities into the Neo4j knowledge graph. Set clear_existing=true for a clean rebuild.",
)
def sync_graph(
    repository_id: int,
    clear_existing: bool = False,
    sync_service: GraphSyncService = Depends(_get_sync_service),
):
    try:
        stats = sync_service.sync_repository(repository_id, clear_existing=clear_existing)
        return GraphSyncResponse(**stats)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Graph sync failed for repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during graph synchronization.",
        )


@router.post(
    "/repositories/{repository_id}/graph/clear",
    summary="Clear repository knowledge graph",
    description="Remove all nodes and relationships for a specific repository from Neo4j.",
)
def clear_graph(
    repository_id: int,
    sync_service: GraphSyncService = Depends(_get_sync_service),
):
    nodes_deleted = sync_service.clear_repository(repository_id)
    return {"repository_id": repository_id, "nodes_deleted": nodes_deleted, "status": "cleared"}


@router.post(
    "/graph/sync-all",
    summary="Sync all repositories to Neo4j",
    description="Build specific knowledge graphs for all active repositories in the database.",
)
def sync_all_graphs(
    clear_existing: bool = False,
    sync_service: GraphSyncService = Depends(_get_sync_service),
):
    results = sync_service.sync_all_repositories(clear_existing=clear_existing)
    return {"total_repositories": len(results), "results": results}


@router.get(
    "/graph/repositories-status",
    summary="Get graph status for all repositories",
    description="Retrieve node counts, relationship counts, and sync status for each repository.",
)
def get_repositories_status(
    db: Session = Depends(get_db),
    query_service: GraphQueryService = Depends(_get_query_service),
):
    from app.repositories.repository_repo import RepositoryRepository
    repo_repo = RepositoryRepository(db)
    repos = repo_repo.get_all_repositories()
    status_list = []
    for r in repos:
        stats = query_service.get_statistics(r.id)
        status_list.append({
            "repository_id": r.id,
            "name": r.name,
            "url": r.url,
            "default_branch": r.default_branch,
            "is_active": r.is_active,
            "has_graph": stats["total_nodes"] > 0,
            "total_nodes": stats["total_nodes"],
            "total_relationships": stats["total_relationships"],
            "node_counts": stats["node_counts"],
        })
    return status_list


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

"""API endpoints for Vector Search & Semantic Retrieval Engine."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.vector_engine.embedding_service import EmbeddingService
from app.engines.vector_engine.search_service import SimilaritySearchService
from app.engines.vector_engine.embedding_providers import get_embedding_provider
from app.schemas.vector import (
    EmbeddingSyncResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
    SearchIndexDetail,
    EmbeddingJobDetail,
)
from app.repositories.vector_repo import VectorRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_embedding_service(db: Session = Depends(get_db)) -> EmbeddingService:
    return EmbeddingService(db)


def _get_search_service(db: Session = Depends(get_db)) -> SimilaritySearchService:
    return SimilaritySearchService(db)


@router.post(
    "/repositories/{repository_id}/embeddings/sync",
    response_model=EmbeddingSyncResponse,
    summary="Sync embeddings for a repository",
    description="Generate or update embeddings for all parsed entities in a repository.",
)
def sync_embeddings(
    repository_id: int,
    service: EmbeddingService = Depends(_get_embedding_service),
):
    try:
        stats = service.sync_embeddings(repository_id)
        return EmbeddingSyncResponse(repository_id=repository_id, **stats)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Embedding sync failed for repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during embedding synchronization.",
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic code search",
    description="Search code entities using natural language queries with cosine similarity.",
)
def search(
    request: SearchRequest,
    service: SimilaritySearchService = Depends(_get_search_service),
):
    results = service.search(
        query=request.query,
        repository_id=request.repository_id,
        entity_type=request.entity_type,
        language=request.language,
        top_k=request.top_k,
    )
    return SearchResponse(
        query=request.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.get(
    "/search/file/{file_id}",
    response_model=SearchResponse,
    summary="Search by file",
    description="Get embeddings related to a specific file.",
)
def search_by_file(
    file_id: int,
    repository_id: int,
    top_k: int = 10,
    service: SimilaritySearchService = Depends(_get_search_service),
):
    results = service.search_by_file(repository_id, file_id, top_k)
    return SearchResponse(
        query=f"file:{file_id}",
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.get(
    "/search/function/{function_id}",
    response_model=SearchResponse,
    summary="Search by function",
    description="Find similar functions to a given function.",
)
def search_by_function(
    function_id: int,
    repository_id: int,
    top_k: int = 10,
    service: SimilaritySearchService = Depends(_get_search_service),
):
    results = service.search_by_function(repository_id, function_id, top_k)
    return SearchResponse(
        query=f"function:{function_id}",
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.get(
    "/search/similar/{entity_name}",
    response_model=SearchResponse,
    summary="Find similar entities",
    description="Find entities semantically similar to a named entity.",
)
def search_similar(
    entity_name: str,
    repository_id: int,
    entity_type: str = "function",
    top_k: int = 10,
    service: SimilaritySearchService = Depends(_get_search_service),
):
    results = service.search_similar_entity(repository_id, entity_type, entity_name, top_k)
    return SearchResponse(
        query=f"similar:{entity_type}:{entity_name}",
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.get(
    "/repositories/{repository_id}/embeddings/status",
    response_model=SearchIndexDetail,
    summary="Get embedding index status",
    description="Get the current status of the embedding index for a repository.",
)
def get_index_status(
    repository_id: int,
    db: Session = Depends(get_db),
):
    vector_repo = VectorRepository(db)
    idx = vector_repo.get_or_create_search_index(repository_id)
    return SearchIndexDetail(
        repository_id=idx.repository_id,
        total_embeddings=idx.total_embeddings,
        total_chunks=idx.total_chunks,
        last_synced_at=idx.last_synced_at,
        last_snapshot_id=idx.last_snapshot_id,
        index_status=idx.index_status,
        dimension=idx.dimension,
        provider=idx.provider,
    )


@router.get(
    "/repositories/{repository_id}/embeddings/jobs",
    response_model=list[EmbeddingJobDetail],
    summary="Get embedding jobs",
    description="Get the history of embedding jobs for a repository.",
)
def get_embedding_jobs(
    repository_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    vector_repo = VectorRepository(db)
    jobs = vector_repo.get_jobs_by_repository(repository_id, limit)
    return [
        EmbeddingJobDetail(
            id=j.id,
            repository_id=j.repository_id,
            status=j.status,
            total_entities=j.total_entities,
            processed_entities=j.processed_entities,
            failed_entities=j.failed_entities,
            skipped_entities=j.skipped_entities,
            embeddings_created=j.embeddings_created,
            embeddings_updated=j.embeddings_updated,
            embeddings_deleted=j.embeddings_deleted,
            duration_seconds=j.duration_seconds,
            error_message=j.error_message,
            retry_count=j.retry_count,
            started_at=j.started_at,
            completed_at=j.completed_at,
        )
        for j in jobs
    ]

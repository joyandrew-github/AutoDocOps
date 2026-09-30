from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.repository_service import RepositoryService
from app.services.git_manager import (
    GitError,
    InvalidRepositoryError,
    AuthenticationError,
    NetworkError,
    RepositoryNotFoundError,
    PermissionDeniedError,
)
from app.schemas.repository import (
    RepositoryConnectRequest,
    RepositoryResponse,
    RepositoryDetailResponse,
    RepositoryScanResponse,
    RepositoryFileResponse,
    DependencyResponse,
    FrameworkResponse,
    ProgrammingLanguageResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> RepositoryService:
    return RepositoryService(db)


@router.post(
    "/repositories/connect",
    response_model=RepositoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect a Git repository",
    description="Clone or pull a Git repository and register it in the database.",
)
def connect_repository(
    request: RepositoryConnectRequest,
    service: RepositoryService = Depends(_get_service),
):
    try:
        repository = service.connect_repository(request.repository_url)
        return repository
    except InvalidRepositoryError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except AuthenticationError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except RepositoryNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except NetworkError as e:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(e))
    except GitError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error connecting repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while connecting the repository.",
        )


@router.post(
    "/repositories/{repository_id}/scan",
    response_model=RepositoryScanResponse,
    summary="Scan a repository",
    description="Run a full scan on a connected repository to detect files, languages, frameworks, and dependencies.",
)
def scan_repository(
    repository_id: int,
    service: RepositoryService = Depends(_get_service),
):
    repo = service.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    try:
        scan = service.scan_repository(repository_id)
        return scan
    except Exception as e:
        logger.error(f"Unexpected error scanning repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during repository scan.",
        )


@router.get(
    "/repositories",
    response_model=list[RepositoryResponse],
    summary="List all repositories",
    description="Retrieve a list of all active repositories enriched with real-time sync and graph status.",
)
def list_repositories(
    db: Session = Depends(get_db),
    service: RepositoryService = Depends(_get_service),
):
    from app.models.github import ConnectedRepository
    from app.models.repository import ProgrammingLanguage
    from app.db.neo4j import get_neo4j_client

    repos = service.get_all_repositories()

    # Query active connected repos
    conn_map: dict[int, ConnectedRepository] = {}
    try:
        conns = db.query(ConnectedRepository).filter(ConnectedRepository.is_active.is_(True)).all()
        for cr in conns:
            if cr.repository_id:
                conn_map[cr.repository_id] = cr
    except Exception as e:
        logger.debug(f"Failed to query connected repositories: {e}")

    # Query graph statistics per repository from Neo4j
    graph_map: dict[int, dict] = {}
    try:
        neo = get_neo4j_client()
        if neo.driver:
            with neo.get_session() as session:
                res = session.run("""
                    MATCH (n) WHERE n.repository_id IS NOT NULL
                    OPTIONAL MATCH (n)-[r]->()
                    RETURN n.repository_id AS repo_id, count(DISTINCT n) AS nodes, count(DISTINCT r) AS rels
                """)
                for row in res:
                    graph_map[row["repo_id"]] = {
                        "nodes": row["nodes"],
                        "rels": row["rels"],
                    }
    except Exception as e:
        logger.debug(f"Failed to query neo4j stats for repositories list: {e}")

    results = []
    for r in repos:
        cr = conn_map.get(r.id)
        latest_scan = service.get_latest_scan(r.id)
        gm = graph_map.get(r.id, {"nodes": 0, "rels": 0})

        langs = [
            l.name for l in db.query(ProgrammingLanguage).filter(ProgrammingLanguage.repository_id == r.id).all()
        ]

        resp = RepositoryResponse(
            id=r.id,
            name=r.name,
            url=r.url,
            local_path=r.local_path,
            default_branch=r.default_branch,
            description=r.description,
            is_active=r.is_active,
            created_at=r.created_at,
            updated_at=r.updated_at,
            sync_status=cr.sync_status if cr else ("synced" if len(r.files) > 0 else "idle"),
            last_synced_at=cr.last_synced_at if cr and cr.last_synced_at else (latest_scan.completed_at if latest_scan else r.updated_at),
            github_connected=bool(cr),
            github_repo_id=cr.id if cr else None,
            github_full_name=cr.full_name if cr else None,
            total_files=len(r.files),
            total_scans=len(r.scans),
            languages=langs,
            graph_nodes=gm["nodes"],
            graph_relationships=gm["rels"],
        )
        results.append(resp)
    return results


@router.get(
    "/repositories/{repository_id}",
    response_model=RepositoryDetailResponse,
    summary="Get repository details",
    description="Retrieve detailed information about a specific repository including its latest scan.",
)
def get_repository(
    repository_id: int,
    service: RepositoryService = Depends(_get_service),
):
    repo = service.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    latest_scan = service.get_latest_scan(repository_id)
    return RepositoryDetailResponse(
        id=repo.id,
        name=repo.name,
        url=repo.url,
        local_path=repo.local_path,
        default_branch=repo.default_branch,
        description=repo.description,
        is_active=repo.is_active,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
        latest_scan=latest_scan,
    )


@router.get(
    "/repositories/{repository_id}/files",
    response_model=list[RepositoryFileResponse],
    summary="Get repository files",
    description="Retrieve all scanned files for a repository.",
)
def get_repository_files(
    repository_id: int,
    service: RepositoryService = Depends(_get_service),
):
    repo = service.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    return service.get_repository_files(repository_id)


@router.get(
    "/repositories/{repository_id}/dependencies",
    response_model=list[DependencyResponse],
    summary="Get repository dependencies",
    description="Retrieve all detected dependencies for a repository.",
)
def get_repository_dependencies(
    repository_id: int,
    service: RepositoryService = Depends(_get_service),
):
    repo = service.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    return service.get_repository_dependencies(repository_id)


@router.get(
    "/repositories/{repository_id}/frameworks",
    response_model=list[FrameworkResponse],
    summary="Get repository frameworks",
    description="Retrieve all detected frameworks for a repository.",
)
def get_repository_frameworks(
    repository_id: int,
    service: RepositoryService = Depends(_get_service),
):
    repo = service.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    return service.get_repository_frameworks(repository_id)


@router.get(
    "/repositories/{repository_id}/languages",
    response_model=list[ProgrammingLanguageResponse],
    summary="Get repository languages",
    description="Retrieve programming language statistics for a repository.",
)
def get_repository_languages(
    repository_id: int,
    service: RepositoryService = Depends(_get_service),
):
    repo = service.get_repository(repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    return service.get_repository_languages(repository_id)

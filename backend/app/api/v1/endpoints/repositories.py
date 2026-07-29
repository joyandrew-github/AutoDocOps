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
    description="Retrieve a list of all connected repositories.",
)
def list_repositories(
    service: RepositoryService = Depends(_get_service),
):
    return service.get_all_repositories()


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

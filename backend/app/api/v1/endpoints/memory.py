from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.memory_engine.snapshot_service import SnapshotService
from app.schemas.memory import (
    GitCommitResponse,
    RepositorySnapshotResponse,
    ChangeSetResponse,
    ChangeSetDetailResponse,
    FileChangeResponse,
    EntityChangeResponse,
    TimelineResponse,
    TimelineEntryResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> SnapshotService:
    return SnapshotService(db)


@router.get(
    "/repositories/{repository_id}/timeline",
    response_model=TimelineResponse,
    summary="Get repository timeline",
    description="Retrieve a chronological timeline of commits, snapshots, and changes.",
)
def get_timeline(
    repository_id: int,
    limit: int = 50,
    service: SnapshotService = Depends(_get_service),
):
    try:
        timeline = service.get_timeline(repository_id, limit)
        entries = []
        for entry in timeline["entries"]:
            entries.append(TimelineEntryResponse(
                commit=entry.get("commit"),
                snapshot=entry.get("snapshot"),
                change_set=entry.get("change_set"),
            ))
        return TimelineResponse(
            repository_id=timeline["repository_id"],
            total_commits=timeline["total_commits"],
            total_snapshots=timeline["total_snapshots"],
            entries=entries,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting timeline for repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the timeline.",
        )


@router.get(
    "/repositories/{repository_id}/commits",
    response_model=list[GitCommitResponse],
    summary="Get repository commits",
    description="Retrieve commit history for a repository.",
)
def get_commits(
    repository_id: int,
    limit: int = 50,
    service: SnapshotService = Depends(_get_service),
):
    return service.get_commits(repository_id, limit)


@router.get(
    "/repositories/{repository_id}/snapshots",
    response_model=list[RepositorySnapshotResponse],
    summary="Get repository snapshots",
    description="Retrieve snapshots for a repository.",
)
def get_snapshots(
    repository_id: int,
    limit: int = 50,
    service: SnapshotService = Depends(_get_service),
):
    return service.get_snapshots(repository_id, limit)


@router.get(
    "/repositories/{repository_id}/changes",
    response_model=list[ChangeSetResponse],
    summary="Get repository change sets",
    description="Retrieve change sets showing differences between snapshots.",
)
def get_changes(
    repository_id: int,
    limit: int = 50,
    service: SnapshotService = Depends(_get_service),
):
    return service.get_changes(repository_id, limit)


@router.get(
    "/repositories/{repository_id}/changes/{commit_hash}",
    response_model=ChangeSetDetailResponse,
    summary="Get changes for a specific commit",
    description="Retrieve detailed file and entity changes for a specific commit.",
)
def get_changes_by_commit(
    repository_id: int,
    commit_hash: str,
    service: SnapshotService = Depends(_get_service),
):
    result = service.get_changes_by_commit(repository_id, commit_hash)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No changes found for commit: {commit_hash}",
        )
    return ChangeSetDetailResponse(
        **ChangeSetResponse.model_validate(result["change_set"]).model_dump(),
        file_changes=[FileChangeResponse.model_validate(fc) for fc in result["file_changes"]],
        entity_changes=[EntityChangeResponse.model_validate(ec) for ec in result["entity_changes"]],
    )

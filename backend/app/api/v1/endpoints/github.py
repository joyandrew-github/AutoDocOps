"""API endpoints for the GitHub Integration & Automation Engine."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.github_engine.github_service import GitHubService
from app.engines.github_engine.webhook_handler import WebhookHandler
from app.schemas.github import (
    GitHubConnectRequest, GitHubConnectResponse, GitHubDisconnectResponse,
    ConnectedRepositoryDetail, GitHubSyncResponse,
    PipelineJobDetail, PullRequestAnalysisDetail, WebhookResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> GitHubService:
    return GitHubService(db)


def _get_webhook_handler(db: Session = Depends(get_db)) -> WebhookHandler:
    return WebhookHandler(db)


@router.post(
    "/github/connect",
    response_model=GitHubConnectResponse,
    summary="Connect a GitHub repository",
)
def connect_repository(
    request: GitHubConnectRequest,
    service: GitHubService = Depends(_get_service),
):
    result = service.connect_repository(
        github_account_id=request.github_account_id,
        github_repo_id=request.github_repo_id,
        full_name=request.full_name,
        repository_id=request.repository_id,
        default_branch=request.default_branch,
        is_private=request.is_private,
    )
    return GitHubConnectResponse(**result)


@router.post(
    "/github/disconnect",
    response_model=GitHubDisconnectResponse,
    summary="Disconnect a repository",
)
def disconnect_repository(
    repo_id: int,
    service: GitHubService = Depends(_get_service),
):
    result = service.disconnect_repository(repo_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return GitHubDisconnectResponse(**result)


@router.get(
    "/github/repositories",
    response_model=list[ConnectedRepositoryDetail],
    summary="List connected repositories",
)
def list_repositories(
    account_id: int,
    service: GitHubService = Depends(_get_service),
):
    repos = service.get_connected_repositories(account_id)
    return [ConnectedRepositoryDetail(**r) for r in repos]


@router.post(
    "/github/repositories/{repo_id}/sync",
    response_model=GitHubSyncResponse,
    summary="Sync a connected repository",
)
def sync_repository(
    repo_id: int,
    service: GitHubService = Depends(_get_service),
):
    result = service.sync_repository(repo_id)
    if result["status"] == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return GitHubSyncResponse(**result)


@router.get(
    "/github/jobs",
    response_model=list[PipelineJobDetail],
    summary="List pipeline jobs",
)
def list_jobs(
    repo_id: int,
    limit: int = 20,
    service: GitHubService = Depends(_get_service),
):
    jobs = service.get_jobs(repo_id, limit)
    return [PipelineJobDetail(**j) for j in jobs]


@router.get(
    "/github/jobs/{job_id}",
    response_model=PipelineJobDetail,
    summary="Get job details",
)
def get_job(
    job_id: int,
    service: GitHubService = Depends(_get_service),
):
    job = service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return PipelineJobDetail(**job)


@router.get(
    "/github/pull-requests/{pr_id}",
    response_model=PullRequestAnalysisDetail,
    summary="Get pull request analysis",
)
def get_pr_analysis(
    pr_id: int,
    service: GitHubService = Depends(_get_service),
):
    pra = service.get_pr_analysis(pr_id)
    if not pra:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PR analysis not found")
    return PullRequestAnalysisDetail(**pra)


@router.post(
    "/github/webhook",
    response_model=WebhookResponse,
    summary="GitHub webhook endpoint",
    description="Receives GitHub webhook events and processes them asynchronously.",
)
async def github_webhook(
    request: Request,
    handler: WebhookHandler = Depends(_get_webhook_handler),
):
    event_type = request.headers.get("X-GitHub-Event", "")
    delivery_id = request.headers.get("X-GitHub-Delivery", "unknown")
    signature = request.headers.get("X-Hub-Signature-256", "")
    raw_body = await request.body()

    try:
        import json
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    logger.info(f"Webhook received: event={event_type} delivery={delivery_id}")
    result = handler.handle_webhook(
        event_type=event_type,
        delivery_id=delivery_id,
        payload=payload,
        signature=signature,
        raw_body=raw_body,
    )
    return WebhookResponse(
        status=result.get("status", "processed"),
        job_id=result.get("job_id"),
        reason=result.get("reason"),
    )

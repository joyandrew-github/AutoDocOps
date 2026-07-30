"""Pydantic schemas for the GitHub Integration Engine."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class GitHubConnectRequest(BaseModel):
    github_account_id: int
    github_repo_id: int
    full_name: str
    repository_id: int | None = None
    default_branch: str = "main"
    is_private: bool = False


class GitHubConnectResponse(BaseModel):
    id: int
    status: str
    webhook_secret: str | None = None


class GitHubDisconnectResponse(BaseModel):
    status: str


class ConnectedRepositoryDetail(BaseModel):
    id: int
    full_name: str
    default_branch: str
    selected_branch: str | None = None
    is_private: bool = False
    auto_sync: bool = True
    sync_status: str = "pending"
    last_synced_at: str | None = None


class GitHubSyncResponse(BaseModel):
    status: str
    sync_id: int | None = None
    duration: float | None = None
    error: str | None = None


class PipelineJobDetail(BaseModel):
    id: int
    job_type: str
    status: str
    attempt: int = 0
    max_retries: int | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
    result: Any | None = None
    created_at: str | None = None


class PullRequestAnalysisDetail(BaseModel):
    id: int
    pr_number: int
    pr_title: str | None = None
    pr_author: str | None = None
    head_branch: str | None = None
    base_branch: str | None = None
    status: str = "pending"
    changed_files: int = 0
    changed_classes: int = 0
    changed_functions: int = 0
    architecture_impact: str | None = None
    documentation_impact: str | None = None
    risk_score: float = 0.0
    risk_level: str = "low"
    breaking_changes: Any | None = None
    recommended_tests: Any | None = None
    summary: str | None = None


class WebhookResponse(BaseModel):
    status: str
    job_id: int | None = None
    reason: str | None = None

"""SQLAlchemy models for the GitHub Integration & Automation Engine."""
from datetime import datetime
from sqlalchemy import (
    String, Integer, Boolean, Float, Text, DateTime, ForeignKey, JSON, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class GitHubAccount(Base, TimestampMixin):
    """GitHub account linked to an AutoDocOps user."""

    __tablename__ = "github_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    github_user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    github_username: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    auth_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pat",
    )  # pat | oauth | app
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[str | None] = mapped_column(Text)
    installation_id: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    connected_repositories: Mapped[list["ConnectedRepository"]] = relationship(
        "ConnectedRepository", back_populates="github_account", cascade="all, delete-orphan",
    )


class ConnectedRepository(Base, TimestampMixin):
    """A GitHub repository connected to AutoDocOps for automatic processing."""

    __tablename__ = "connected_repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    github_account_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("github_accounts.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    repository_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="SET NULL"), index=True,
    )
    github_repo_id: Mapped[int] = mapped_column(Integer, nullable=False)
    full_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    default_branch: Mapped[str] = mapped_column(String(100), default="main")
    selected_branch: Mapped[str | None] = mapped_column(String(100))
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    webhook_id: Mapped[int | None] = mapped_column(Integer)
    webhook_secret: Mapped[str | None] = mapped_column(String(255))
    auto_sync: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    github_account: Mapped["GitHubAccount"] = relationship(
        "GitHubAccount", back_populates="connected_repositories",
    )


class WebhookEvent(Base, TimestampMixin):
    """Record of a received GitHub webhook event."""

    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str | None] = mapped_column(String(100))
    delivery_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    repository_full_name: Mapped[str | None] = mapped_column(String(500), index=True)
    sender: Mapped[str | None] = mapped_column(String(255))
    ref: Mapped[str | None] = mapped_column(String(500))
    payload: Mapped[dict | None] = mapped_column(JSON)
    signature_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default="received", index=True)
    error_message: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PipelineJob(Base, TimestampMixin):
    """Background pipeline job triggered by a webhook or manual sync."""

    __tablename__ = "pipeline_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connected_repository_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("connected_repositories.id", ondelete="SET NULL"), index=True,
    )
    webhook_event_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("webhook_events.id", ondelete="SET NULL"),
    )
    job_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    attempt: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    result: Mapped[dict | None] = mapped_column(JSON)
    error_message: Mapped[str | None] = mapped_column(Text)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSON)


class PullRequestAnalysis(Base, TimestampMixin):
    """Analysis results for a GitHub pull request."""

    __tablename__ = "pull_request_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connected_repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("connected_repositories.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    pr_number: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    pr_title: Mapped[str | None] = mapped_column(String(500))
    pr_author: Mapped[str | None] = mapped_column(String(255))
    head_branch: Mapped[str | None] = mapped_column(String(255))
    base_branch: Mapped[str | None] = mapped_column(String(255))
    head_sha: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    changed_files: Mapped[int] = mapped_column(Integer, default=0)
    changed_classes: Mapped[int] = mapped_column(Integer, default=0)
    changed_functions: Mapped[int] = mapped_column(Integer, default=0)
    architecture_impact: Mapped[str | None] = mapped_column(Text)
    documentation_impact: Mapped[str | None] = mapped_column(Text)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(50), default="low")
    breaking_changes: Mapped[dict | None] = mapped_column(JSON)
    recommended_tests: Mapped[dict | None] = mapped_column(JSON)
    summary: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RepositorySync(Base, TimestampMixin):
    """Record of a repository sync operation."""

    __tablename__ = "repository_syncs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    connected_repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("connected_repositories.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    sync_type: Mapped[str] = mapped_column(String(50), default="manual")
    branch: Mapped[str | None] = mapped_column(String(100))
    commit_hash: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    entities_changed: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    pipeline_steps: Mapped[dict | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

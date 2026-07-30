"""GitHub Integration & Automation Engine

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-30
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_accounts",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("github_user_id", sa.Integer(), nullable=False, unique=True),
        sa.Column("github_username", sa.String(255), nullable=False, index=True),
        sa.Column("avatar_url", sa.String(500)),
        sa.Column("auth_type", sa.String(50), nullable=False, server_default="pat"),
        sa.Column("access_token_encrypted", sa.Text()),
        sa.Column("refresh_token_encrypted", sa.Text()),
        sa.Column("token_expires_at", sa.DateTime(timezone=True)),
        sa.Column("scopes", sa.Text()),
        sa.Column("installation_id", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "connected_repositories",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("github_account_id", sa.Integer(), sa.ForeignKey("github_accounts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="SET NULL"), index=True),
        sa.Column("github_repo_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(500), nullable=False, index=True),
        sa.Column("default_branch", sa.String(100), server_default="main"),
        sa.Column("selected_branch", sa.String(100)),
        sa.Column("is_private", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("webhook_id", sa.Integer()),
        sa.Column("webhook_secret", sa.String(255)),
        sa.Column("auto_sync", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("sync_status", sa.String(50), server_default="pending"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("event_type", sa.String(100), nullable=False, index=True),
        sa.Column("action", sa.String(100)),
        sa.Column("delivery_id", sa.String(100), unique=True, nullable=False),
        sa.Column("repository_full_name", sa.String(500), index=True),
        sa.Column("sender", sa.String(255)),
        sa.Column("ref", sa.String(500)),
        sa.Column("payload", sa.JSON()),
        sa.Column("signature_valid", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("status", sa.String(50), server_default="received", index=True),
        sa.Column("error_message", sa.Text()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pipeline_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("connected_repository_id", sa.Integer(), sa.ForeignKey("connected_repositories.id", ondelete="SET NULL"), index=True),
        sa.Column("webhook_event_id", sa.Integer(), sa.ForeignKey("webhook_events.id", ondelete="SET NULL")),
        sa.Column("job_type", sa.String(100), nullable=False, index=True),
        sa.Column("status", sa.String(50), server_default="queued", index=True),
        sa.Column("priority", sa.Integer(), server_default=sa.text("5")),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("0")),
        sa.Column("max_retries", sa.Integer(), server_default=sa.text("3")),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("result", sa.JSON()),
        sa.Column("error_message", sa.Text()),
        sa.Column("metadata", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "pull_request_analyses",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("connected_repository_id", sa.Integer(), sa.ForeignKey("connected_repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("pr_number", sa.Integer(), nullable=False, index=True),
        sa.Column("pr_title", sa.String(500)),
        sa.Column("pr_author", sa.String(255)),
        sa.Column("head_branch", sa.String(255)),
        sa.Column("base_branch", sa.String(255)),
        sa.Column("head_sha", sa.String(100)),
        sa.Column("status", sa.String(50), server_default="pending", index=True),
        sa.Column("changed_files", sa.Integer(), server_default=sa.text("0")),
        sa.Column("changed_classes", sa.Integer(), server_default=sa.text("0")),
        sa.Column("changed_functions", sa.Integer(), server_default=sa.text("0")),
        sa.Column("architecture_impact", sa.Text()),
        sa.Column("documentation_impact", sa.Text()),
        sa.Column("risk_score", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("risk_level", sa.String(50), server_default="low"),
        sa.Column("breaking_changes", sa.JSON()),
        sa.Column("recommended_tests", sa.JSON()),
        sa.Column("summary", sa.Text()),
        sa.Column("details", sa.JSON()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "repository_syncs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("connected_repository_id", sa.Integer(), sa.ForeignKey("connected_repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("sync_type", sa.String(50), server_default="manual"),
        sa.Column("branch", sa.String(100)),
        sa.Column("commit_hash", sa.String(100)),
        sa.Column("status", sa.String(50), server_default="pending", index=True),
        sa.Column("files_changed", sa.Integer(), server_default=sa.text("0")),
        sa.Column("entities_changed", sa.Integer(), server_default=sa.text("0")),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("pipeline_steps", sa.JSON()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("repository_syncs")
    op.drop_table("pull_request_analyses")
    op.drop_table("pipeline_jobs")
    op.drop_table("webhook_events")
    op.drop_table("connected_repositories")
    op.drop_table("github_accounts")

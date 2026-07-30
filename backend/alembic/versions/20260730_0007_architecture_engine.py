"""architecture intelligence engine

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "architecture_models",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("model_type", sa.String(50), nullable=False, index=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("data", sa.JSON()),
        sa.Column("content_hash", sa.String(64), index=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "architecture_diagrams",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("model_id", sa.Integer(), sa.ForeignKey("architecture_models.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("diagram_type", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("format", sa.String(20), nullable=False, server_default="mermaid"),
        sa.Column("content", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "architecture_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("total_models", sa.Integer(), server_default="0"),
        sa.Column("models_created", sa.Integer(), server_default="0"),
        sa.Column("models_updated", sa.Integer(), server_default="0"),
        sa.Column("models_skipped", sa.Integer(), server_default="0"),
        sa.Column("diagrams_generated", sa.Integer(), server_default="0"),
        sa.Column("violations_detected", sa.Integer(), server_default="0"),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "architecture_violations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("violation_type", sa.String(50), nullable=False, index=True),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("source_entity", sa.String(500)),
        sa.Column("target_entity", sa.String(500)),
        sa.Column("source_file", sa.String(1000)),
        sa.Column("target_file", sa.String(1000)),
        sa.Column("source_layer", sa.String(100)),
        sa.Column("target_layer", sa.String(100)),
        sa.Column("is_resolved", sa.Boolean(), server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_arch_models_repo_type", "architecture_models", ["repository_id", "model_type"])
    op.create_index("ix_arch_violations_repo_type", "architecture_violations", ["repository_id", "violation_type"])


def downgrade() -> None:
    op.drop_index("ix_arch_violations_repo_type")
    op.drop_index("ix_arch_models_repo_type")
    op.drop_table("architecture_violations")
    op.drop_table("architecture_snapshots")
    op.drop_table("architecture_diagrams")
    op.drop_table("architecture_models")

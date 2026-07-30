"""impact analysis engine

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "impact_analyses",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("trigger_type", sa.String(50), nullable=False, server_default="manual"),
        sa.Column("commit_hash", sa.String(64)),
        sa.Column("snapshot_id", sa.Integer()),
        sa.Column("total_changes", sa.Integer(), server_default="0"),
        sa.Column("total_affected", sa.Integer(), server_default="0"),
        sa.Column("overall_risk_level", sa.String(20), server_default="low"),
        sa.Column("overall_risk_score", sa.Float(), server_default="0.0"),
        sa.Column("summary", sa.Text()),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "impact_results",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000)),
        sa.Column("change_type", sa.String(50), nullable=False, server_default="modified"),
        sa.Column("impact_type", sa.String(50), nullable=False, server_default="direct"),
        sa.Column("risk_level", sa.String(20), server_default="low"),
        sa.Column("risk_score", sa.Float(), server_default="0.0"),
        sa.Column("direct_dependents", sa.Integer(), server_default="0"),
        sa.Column("indirect_dependents", sa.Integer(), server_default="0"),
        sa.Column("affected_tests", sa.Text()),
        sa.Column("recommendations", sa.Text()),
        sa.Column("details", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "impact_relationships",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("result_id", sa.Integer(), sa.ForeignKey("impact_results.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("relationship_type", sa.String(50), nullable=False),
        sa.Column("source_entity", sa.String(500), nullable=False),
        sa.Column("target_entity", sa.String(500), nullable=False),
        sa.Column("source_file", sa.String(1000)),
        sa.Column("target_file", sa.String(1000)),
        sa.Column("depth", sa.Integer(), server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("analysis_id", sa.Integer(), sa.ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("dependency_score", sa.Float(), server_default="0.0"),
        sa.Column("api_score", sa.Float(), server_default="0.0"),
        sa.Column("cross_module_score", sa.Float(), server_default="0.0"),
        sa.Column("circular_dep_score", sa.Float(), server_default="0.0"),
        sa.Column("change_frequency_score", sa.Float(), server_default="0.0"),
        sa.Column("architecture_score", sa.Float(), server_default="0.0"),
        sa.Column("test_recommendations", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("factors", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_impact_repo_status", "impact_analyses", ["repository_id", "status"])
    op.create_index("ix_impact_results_entity", "impact_results", ["analysis_id", "entity_type"])


def downgrade() -> None:
    op.drop_index("ix_impact_results_entity")
    op.drop_index("ix_impact_repo_status")
    op.drop_table("risk_assessments")
    op.drop_table("impact_relationships")
    op.drop_table("impact_results")
    op.drop_table("impact_analyses")

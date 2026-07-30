"""documentation engine

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "documentations",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("doc_type", sa.String(50), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), index=True),
        sa.Column("entity_name", sa.String(500)),
        sa.Column("file_path", sa.String(1000)),
        sa.Column("content", sa.Text()),
        sa.Column("summary", sa.Text()),
        sa.Column("content_hash", sa.String(64), index=True),
        sa.Column("format", sa.String(20), server_default="markdown"),
        sa.Column("is_published", sa.Boolean(), server_default="true"),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("language", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "documentation_versions",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("documentation_id", sa.Integer(), sa.ForeignKey("documentations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("change_summary", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "documentation_sections",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("documentation_id", sa.Integer(), sa.ForeignKey("documentations.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text()),
        sa.Column("section_order", sa.Integer(), server_default="0"),
        sa.Column("section_type", sa.String(50), server_default="content"),
        sa.Column("level", sa.Integer(), server_default="2"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "documentation_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("doc_types_requested", sa.Text()),
        sa.Column("total_documents", sa.Integer(), server_default="0"),
        sa.Column("documents_created", sa.Integer(), server_default="0"),
        sa.Column("documents_updated", sa.Integer(), server_default="0"),
        sa.Column("documents_skipped", sa.Integer(), server_default="0"),
        sa.Column("documents_failed", sa.Integer(), server_default="0"),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_docs_repo_type", "documentations", ["repository_id", "doc_type"])
    op.create_index("ix_docs_repo_slug", "documentations", ["repository_id", "slug"])


def downgrade() -> None:
    op.drop_index("ix_docs_repo_slug")
    op.drop_index("ix_docs_repo_type")
    op.drop_table("documentation_jobs")
    op.drop_table("documentation_sections")
    op.drop_table("documentation_versions")
    op.drop_table("documentations")

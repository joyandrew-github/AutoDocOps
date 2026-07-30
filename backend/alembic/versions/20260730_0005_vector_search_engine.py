"""vector search engine

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # --- embeddings ---
    op.create_table(
        "embeddings",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_id", sa.Integer(), index=True),
        sa.Column("entity_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000)),
        sa.Column("content_hash", sa.String(64), index=True),
        sa.Column("embedding_text", sa.Text()),
        sa.Column("token_count", sa.Integer(), default=0),
        sa.Column("language", sa.String(100), index=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="mock"),
        sa.Column("model", sa.String(100)),
        sa.Column("dimension", sa.Integer(), default=1536),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- code_chunks ---
    op.create_table(
        "code_chunks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("embedding_id", sa.Integer(), sa.ForeignKey("embeddings.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), default=0),
        sa.Column("entity_type", sa.String(50), nullable=False, index=True),
        sa.Column("entity_name", sa.String(500), nullable=False),
        sa.Column("file_path", sa.String(1000)),
        sa.Column("language", sa.String(100), index=True),
        sa.Column("start_line", sa.Integer()),
        sa.Column("end_line", sa.Integer()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- search_indexes ---
    op.create_table(
        "search_indexes",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, unique=True, index=True),
        sa.Column("total_embeddings", sa.Integer(), default=0),
        sa.Column("total_chunks", sa.Integer(), default=0),
        sa.Column("last_synced_at", sa.DateTime(timezone=True)),
        sa.Column("last_snapshot_id", sa.Integer()),
        sa.Column("index_status", sa.String(50), server_default="pending"),
        sa.Column("dimension", sa.Integer(), default=1536),
        sa.Column("provider", sa.String(50), server_default="mock"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- embedding_jobs ---
    op.create_table(
        "embedding_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("repository_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending", index=True),
        sa.Column("total_entities", sa.Integer(), default=0),
        sa.Column("processed_entities", sa.Integer(), default=0),
        sa.Column("failed_entities", sa.Integer(), default=0),
        sa.Column("skipped_entities", sa.Integer(), default=0),
        sa.Column("embeddings_created", sa.Integer(), default=0),
        sa.Column("embeddings_updated", sa.Integer(), default=0),
        sa.Column("embeddings_deleted", sa.Integer(), default=0),
        sa.Column("duration_seconds", sa.Float()),
        sa.Column("error_message", sa.Text()),
        sa.Column("retry_count", sa.Integer(), default=0),
        sa.Column("max_retries", sa.Integer(), default=3),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create composite indexes for efficient search queries
    op.create_index("ix_embeddings_repo_entity_type", "embeddings", ["repository_id", "entity_type"])
    op.create_index("ix_embeddings_repo_hash", "embeddings", ["repository_id", "content_hash"])
    op.create_index("ix_code_chunks_repo_entity_type", "code_chunks", ["repository_id", "entity_type"])
    op.create_index("ix_code_chunks_repo_language", "code_chunks", ["repository_id", "language"])


def downgrade() -> None:
    op.drop_index("ix_code_chunks_repo_language")
    op.drop_index("ix_code_chunks_repo_entity_type")
    op.drop_index("ix_embeddings_repo_hash")
    op.drop_index("ix_embeddings_repo_entity_type")
    op.drop_table("embedding_jobs")
    op.drop_table("search_indexes")
    op.drop_table("code_chunks")
    op.drop_table("embeddings")
    op.execute("DROP EXTENSION IF EXISTS vector")

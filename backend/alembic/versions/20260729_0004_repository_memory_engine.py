"""repository memory engine

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # git_commits
    op.create_table(
        'git_commits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('commit_hash', sa.String(length=40), nullable=False),
        sa.Column('parent_hash', sa.String(length=40), nullable=True),
        sa.Column('author_name', sa.String(length=255), nullable=True),
        sa.Column('author_email', sa.String(length=255), nullable=True),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('branch', sa.String(length=255), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_git_commits_id'), 'git_commits', ['id'], unique=False)
    op.create_index(op.f('ix_git_commits_repository_id'), 'git_commits', ['repository_id'], unique=False)
    op.create_index(op.f('ix_git_commits_commit_hash'), 'git_commits', ['commit_hash'], unique=False)

    # repository_snapshots
    op.create_table(
        'repository_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('commit_id', sa.Integer(), nullable=True),
        sa.Column('parser_run_id', sa.Integer(), nullable=True),
        sa.Column('commit_hash', sa.String(length=40), nullable=True),
        sa.Column('total_files', sa.Integer(), server_default='0'),
        sa.Column('total_classes', sa.Integer(), server_default='0'),
        sa.Column('total_functions', sa.Integer(), server_default='0'),
        sa.Column('total_methods', sa.Integer(), server_default='0'),
        sa.Column('total_imports', sa.Integer(), server_default='0'),
        sa.Column('total_variables', sa.Integer(), server_default='0'),
        sa.Column('snapshot_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['commit_id'], ['git_commits.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['parser_run_id'], ['parser_runs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repository_snapshots_id'), 'repository_snapshots', ['id'], unique=False)
    op.create_index(op.f('ix_repository_snapshots_repository_id'), 'repository_snapshots', ['repository_id'], unique=False)
    op.create_index(op.f('ix_repository_snapshots_commit_id'), 'repository_snapshots', ['commit_id'], unique=False)
    op.create_index(op.f('ix_repository_snapshots_parser_run_id'), 'repository_snapshots', ['parser_run_id'], unique=False)

    # entity_versions
    op.create_table(
        'entity_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_name', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=True),
        sa.Column('end_line', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=False, server_default='created'),
        sa.Column('previous_version_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['previous_version_id'], ['entity_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entity_versions_id'), 'entity_versions', ['id'], unique=False)
    op.create_index(op.f('ix_entity_versions_repository_id'), 'entity_versions', ['repository_id'], unique=False)
    op.create_index(op.f('ix_entity_versions_snapshot_id'), 'entity_versions', ['snapshot_id'], unique=False)
    op.create_index(op.f('ix_entity_versions_entity_type'), 'entity_versions', ['entity_type'], unique=False)

    # change_sets
    op.create_table(
        'change_sets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_id', sa.Integer(), nullable=False),
        sa.Column('previous_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('commit_hash', sa.String(length=40), nullable=True),
        sa.Column('total_file_changes', sa.Integer(), server_default='0'),
        sa.Column('total_entity_changes', sa.Integer(), server_default='0'),
        sa.Column('files_added', sa.Integer(), server_default='0'),
        sa.Column('files_modified', sa.Integer(), server_default='0'),
        sa.Column('files_deleted', sa.Integer(), server_default='0'),
        sa.Column('files_renamed', sa.Integer(), server_default='0'),
        sa.Column('entities_added', sa.Integer(), server_default='0'),
        sa.Column('entities_modified', sa.Integer(), server_default='0'),
        sa.Column('entities_deleted', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['previous_snapshot_id'], ['repository_snapshots.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['snapshot_id'], ['repository_snapshots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_change_sets_id'), 'change_sets', ['id'], unique=False)
    op.create_index(op.f('ix_change_sets_repository_id'), 'change_sets', ['repository_id'], unique=False)
    op.create_index(op.f('ix_change_sets_snapshot_id'), 'change_sets', ['snapshot_id'], unique=False)

    # file_changes
    op.create_table(
        'file_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('change_set_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('previous_path', sa.String(length=1000), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('previous_checksum', sa.String(length=64), nullable=True),
        sa.Column('current_checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['change_set_id'], ['change_sets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_changes_id'), 'file_changes', ['id'], unique=False)
    op.create_index(op.f('ix_file_changes_change_set_id'), 'file_changes', ['change_set_id'], unique=False)

    # entity_changes
    op.create_table(
        'entity_changes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('change_set_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_name', sa.String(length=500), nullable=False),
        sa.Column('file_path', sa.String(length=1000), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('previous_name', sa.String(length=500), nullable=True),
        sa.Column('previous_file_path', sa.String(length=1000), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['change_set_id'], ['change_sets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_entity_changes_id'), 'entity_changes', ['id'], unique=False)
    op.create_index(op.f('ix_entity_changes_change_set_id'), 'entity_changes', ['change_set_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_entity_changes_change_set_id'), table_name='entity_changes')
    op.drop_index(op.f('ix_entity_changes_id'), table_name='entity_changes')
    op.drop_table('entity_changes')

    op.drop_index(op.f('ix_file_changes_change_set_id'), table_name='file_changes')
    op.drop_index(op.f('ix_file_changes_id'), table_name='file_changes')
    op.drop_table('file_changes')

    op.drop_index(op.f('ix_change_sets_snapshot_id'), table_name='change_sets')
    op.drop_index(op.f('ix_change_sets_repository_id'), table_name='change_sets')
    op.drop_index(op.f('ix_change_sets_id'), table_name='change_sets')
    op.drop_table('change_sets')

    op.drop_index(op.f('ix_entity_versions_entity_type'), table_name='entity_versions')
    op.drop_index(op.f('ix_entity_versions_snapshot_id'), table_name='entity_versions')
    op.drop_index(op.f('ix_entity_versions_repository_id'), table_name='entity_versions')
    op.drop_index(op.f('ix_entity_versions_id'), table_name='entity_versions')
    op.drop_table('entity_versions')

    op.drop_index(op.f('ix_repository_snapshots_parser_run_id'), table_name='repository_snapshots')
    op.drop_index(op.f('ix_repository_snapshots_commit_id'), table_name='repository_snapshots')
    op.drop_index(op.f('ix_repository_snapshots_repository_id'), table_name='repository_snapshots')
    op.drop_index(op.f('ix_repository_snapshots_id'), table_name='repository_snapshots')
    op.drop_table('repository_snapshots')

    op.drop_index(op.f('ix_git_commits_commit_hash'), table_name='git_commits')
    op.drop_index(op.f('ix_git_commits_repository_id'), table_name='git_commits')
    op.drop_index(op.f('ix_git_commits_id'), table_name='git_commits')
    op.drop_table('git_commits')

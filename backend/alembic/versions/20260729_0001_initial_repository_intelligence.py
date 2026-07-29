"""initial repository intelligence models

Revision ID: 0001
Revises: 
Create Date: 2026-07-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'])
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Repositories table
    op.create_table(
        'repositories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('local_path', sa.String(length=500), nullable=False),
        sa.Column('default_branch', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_repositories_id'), 'repositories', ['id'])
    op.create_index(op.f('ix_repositories_url'), 'repositories', ['url'], unique=True)

    # Repository scans table
    op.create_table(
        'repository_scans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_files', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('languages_detected', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('frameworks_detected', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('dependencies_detected', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_repository_scans_id'), 'repository_scans', ['id'])
    op.create_index(op.f('ix_repository_scans_repository_id'), 'repository_scans', ['repository_id'])

    # Repository files table
    op.create_table(
        'repository_files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('relative_path', sa.String(length=1000), nullable=False),
        sa.Column('absolute_path', sa.String(length=1000), nullable=False),
        sa.Column('extension', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sha256_checksum', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['repository_scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_repository_files_id'), 'repository_files', ['id'])
    op.create_index(op.f('ix_repository_files_repository_id'), 'repository_files', ['repository_id'])
    op.create_index(op.f('ix_repository_files_scan_id'), 'repository_files', ['scan_id'])
    op.create_index(op.f('ix_repository_files_language'), 'repository_files', ['language'])

    # Programming languages table
    op.create_table(
        'programming_languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('file_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_size_bytes', sa.BigInteger(), nullable=True, server_default='0'),
        sa.Column('percentage', sa.Float(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['repository_scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_programming_languages_id'), 'programming_languages', ['id'])
    op.create_index(op.f('ix_programming_languages_repository_id'), 'programming_languages', ['repository_id'])
    op.create_index(op.f('ix_programming_languages_scan_id'), 'programming_languages', ['scan_id'])

    # Frameworks table
    op.create_table(
        'frameworks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=True),
        sa.Column('confidence', sa.String(length=20), nullable=True, server_default='high'),
        sa.Column('detected_by', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['repository_scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_frameworks_id'), 'frameworks', ['id'])
    op.create_index(op.f('ix_frameworks_repository_id'), 'frameworks', ['repository_id'])
    op.create_index(op.f('ix_frameworks_scan_id'), 'frameworks', ['scan_id'])

    # Dependencies table
    op.create_table(
        'dependencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('scan_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=100), nullable=True),
        sa.Column('package_manager', sa.String(length=100), nullable=False),
        sa.Column('source_file', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scan_id'], ['repository_scans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_dependencies_id'), 'dependencies', ['id'])
    op.create_index(op.f('ix_dependencies_repository_id'), 'dependencies', ['repository_id'])
    op.create_index(op.f('ix_dependencies_scan_id'), 'dependencies', ['scan_id'])


def downgrade() -> None:
    op.drop_table('dependencies')
    op.drop_table('frameworks')
    op.drop_table('programming_languages')
    op.drop_table('repository_files')
    op.drop_table('repository_scans')
    op.drop_table('repositories')
    op.drop_table('users')

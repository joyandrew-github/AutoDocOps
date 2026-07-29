"""incremental parsing with SHA256 checksums

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add incremental parsing fields to parser_runs
    op.add_column('parser_runs', sa.Column('files_parsed', sa.Integer(), server_default='0', nullable=False))
    op.add_column('parser_runs', sa.Column('files_skipped', sa.Integer(), server_default='0', nullable=False))
    op.add_column('parser_runs', sa.Column('files_failed', sa.Integer(), server_default='0', nullable=False))
    op.add_column('parser_runs', sa.Column('parser_version', sa.String(length=50), server_default='1.0.0', nullable=False))

    # Create file_parse_statuses table
    op.create_table(
        'file_parse_statuses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parser_run_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('previous_checksum', sa.String(length=64), nullable=True),
        sa.Column('parsed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('nodes_extracted', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parser_run_id'], ['parser_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_file_parse_statuses_file_id'), 'file_parse_statuses', ['file_id'], unique=False)
    op.create_index(op.f('ix_file_parse_statuses_parser_run_id'), 'file_parse_statuses', ['parser_run_id'], unique=False)


def downgrade() -> None:
    # Remove file_parse_statuses table
    op.drop_index(op.f('ix_file_parse_statuses_parser_run_id'), table_name='file_parse_statuses')
    op.drop_index(op.f('ix_file_parse_statuses_file_id'), table_name='file_parse_statuses')
    op.drop_table('file_parse_statuses')

    # Remove incremental parsing fields from parser_runs
    op.drop_column('parser_runs', 'parser_version')
    op.drop_column('parser_runs', 'files_failed')
    op.drop_column('parser_runs', 'files_skipped')
    op.drop_column('parser_runs', 'files_parsed')

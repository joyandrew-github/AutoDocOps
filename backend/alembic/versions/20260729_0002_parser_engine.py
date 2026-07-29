"""parser engine models

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-29

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # parser_runs
    op.create_table(
        'parser_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('repository_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_files_parsed', sa.Integer(), server_default='0'),
        sa.Column('total_nodes_extracted', sa.Integer(), server_default='0'),
        sa.Column('total_functions', sa.Integer(), server_default='0'),
        sa.Column('total_classes', sa.Integer(), server_default='0'),
        sa.Column('total_imports', sa.Integer(), server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_parser_runs_id'), 'parser_runs', ['id'])
    op.create_index(op.f('ix_parser_runs_repository_id'), 'parser_runs', ['repository_id'])

    # ast_nodes (base table for polymorphic inheritance)
    op.create_table(
        'ast_nodes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('parser_run_id', sa.Integer(), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('start_line', sa.Integer(), nullable=True),
        sa.Column('end_line', sa.Integer(), nullable=True),
        sa.Column('start_column', sa.Integer(), nullable=True),
        sa.Column('end_column', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['repository_files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parser_run_id'], ['parser_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ast_nodes_id'), 'ast_nodes', ['id'])
    op.create_index(op.f('ix_ast_nodes_file_id'), 'ast_nodes', ['file_id'])
    op.create_index(op.f('ix_ast_nodes_parser_run_id'), 'ast_nodes', ['parser_run_id'])
    op.create_index(op.f('ix_ast_nodes_node_type'), 'ast_nodes', ['node_type'])

    # functions
    op.create_table(
        'functions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.Column('return_type', sa.String(length=500), nullable=True),
        sa.Column('decorators', sa.Text(), nullable=True),
        sa.Column('is_async', sa.Boolean(), server_default='false'),
        sa.Column('is_generator', sa.Boolean(), server_default='false'),
        sa.Column('docstring', sa.Text(), nullable=True),
        sa.Column('body_start_line', sa.Integer(), nullable=True),
        sa.Column('body_end_line', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # classes
    op.create_table(
        'classes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('bases', sa.Text(), nullable=True),
        sa.Column('decorators', sa.Text(), nullable=True),
        sa.Column('docstring', sa.Text(), nullable=True),
        sa.Column('is_abstract', sa.Boolean(), server_default='false'),
        sa.Column('interfaces', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # methods
    op.create_table(
        'methods',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('class_name', sa.String(length=500), nullable=True),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.Column('return_type', sa.String(length=500), nullable=True),
        sa.Column('decorators', sa.Text(), nullable=True),
        sa.Column('is_async', sa.Boolean(), server_default='false'),
        sa.Column('is_static', sa.Boolean(), server_default='false'),
        sa.Column('is_constructor', sa.Boolean(), server_default='false'),
        sa.Column('docstring', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # imports
    op.create_table(
        'imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('module', sa.String(length=500), nullable=True),
        sa.Column('alias', sa.String(length=255), nullable=True),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('is_wildcard', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # exports
    op.create_table(
        'exports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('exported_type', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # variables
    op.create_table(
        'variables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('var_type', sa.String(length=500), nullable=True),
        sa.Column('is_constant', sa.Boolean(), server_default='false'),
        sa.Column('scope', sa.String(length=50), nullable=True),
        sa.Column('initial_value', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    # comments
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('comment_type', sa.String(length=50), nullable=True),
        sa.Column('is_docstring', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['id'], ['ast_nodes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('comments')
    op.drop_table('variables')
    op.drop_table('exports')
    op.drop_table('imports')
    op.drop_table('methods')
    op.drop_table('classes')
    op.drop_table('functions')
    op.drop_index(op.f('ix_ast_nodes_node_type'), table_name='ast_nodes')
    op.drop_index(op.f('ix_ast_nodes_parser_run_id'), table_name='ast_nodes')
    op.drop_index(op.f('ix_ast_nodes_file_id'), table_name='ast_nodes')
    op.drop_index(op.f('ix_ast_nodes_id'), table_name='ast_nodes')
    op.drop_table('ast_nodes')
    op.drop_index(op.f('ix_parser_runs_repository_id'), table_name='parser_runs')
    op.drop_index(op.f('ix_parser_runs_id'), table_name='parser_runs')
    op.drop_table('parser_runs')

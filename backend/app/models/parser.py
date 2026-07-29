from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Float, Text, DateTime, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ParserRun(Base, TimestampMixin):
    """Model representing a single parser execution run."""

    __tablename__ = "parser_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_files_parsed: Mapped[int] = mapped_column(Integer, default=0)
    total_nodes_extracted: Mapped[int] = mapped_column(Integer, default=0)
    total_functions: Mapped[int] = mapped_column(Integer, default=0)
    total_classes: Mapped[int] = mapped_column(Integer, default=0)
    total_imports: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Incremental parsing fields
    files_parsed: Mapped[int] = mapped_column(Integer, default=0)
    files_skipped: Mapped[int] = mapped_column(Integer, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, default=0)
    parser_version: Mapped[str] = mapped_column(String(50), default="1.0.0")

    ast_nodes: Mapped[list["ASTNode"]] = relationship(
        "ASTNode", back_populates="parser_run", cascade="all, delete-orphan"
    )
    file_parse_statuses: Mapped[list["FileParseStatus"]] = relationship(
        "FileParseStatus", back_populates="parser_run", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ParserRun(id={self.id}, repo_id={self.repository_id}, status={self.status})>"


class ASTNode(Base, TimestampMixin):
    """Base model for all AST nodes extracted from source files."""

    __tablename__ = "ast_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parser_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parser_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    node_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(500))
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    start_column: Mapped[int | None] = mapped_column(Integer)
    end_column: Mapped[int | None] = mapped_column(Integer)

    parser_run: Mapped["ParserRun"] = relationship("ParserRun", back_populates="ast_nodes")

    __mapper_args__ = {
        "polymorphic_on": "node_type",
        "polymorphic_identity": "ast_node",
    }

    def __repr__(self) -> str:
        return f"<ASTNode(id={self.id}, type={self.node_type}, name={self.name})>"


class Function(ASTNode):
    """Model for extracted function definitions."""

    __tablename__ = "functions"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    parameters: Mapped[str | None] = mapped_column(Text)
    return_type: Mapped[str | None] = mapped_column(String(500))
    decorators: Mapped[str | None] = mapped_column(Text)
    is_async: Mapped[bool] = mapped_column(Boolean, default=False)
    is_generator: Mapped[bool] = mapped_column(Boolean, default=False)
    docstring: Mapped[str | None] = mapped_column(Text)
    body_start_line: Mapped[int | None] = mapped_column(Integer)
    body_end_line: Mapped[int | None] = mapped_column(Integer)

    __mapper_args__ = {
        "polymorphic_identity": "function",
    }

    def __repr__(self) -> str:
        return f"<Function(id={self.id}, name={self.name})>"


class Class(ASTNode):
    """Model for extracted class definitions."""

    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    bases: Mapped[str | None] = mapped_column(Text)
    decorators: Mapped[str | None] = mapped_column(Text)
    docstring: Mapped[str | None] = mapped_column(Text)
    is_abstract: Mapped[bool] = mapped_column(Boolean, default=False)
    interfaces: Mapped[str | None] = mapped_column(Text)

    __mapper_args__ = {
        "polymorphic_identity": "class",
    }

    def __repr__(self) -> str:
        return f"<Class(id={self.id}, name={self.name})>"


class Method(ASTNode):
    """Model for extracted method definitions (within classes)."""

    __tablename__ = "methods"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    class_name: Mapped[str | None] = mapped_column(String(500))
    parameters: Mapped[str | None] = mapped_column(Text)
    return_type: Mapped[str | None] = mapped_column(String(500))
    decorators: Mapped[str | None] = mapped_column(Text)
    is_async: Mapped[bool] = mapped_column(Boolean, default=False)
    is_static: Mapped[bool] = mapped_column(Boolean, default=False)
    is_constructor: Mapped[bool] = mapped_column(Boolean, default=False)
    docstring: Mapped[str | None] = mapped_column(Text)

    __mapper_args__ = {
        "polymorphic_identity": "method",
    }

    def __repr__(self) -> str:
        return f"<Method(id={self.id}, class={self.class_name}, name={self.name})>"


class Import(ASTNode):
    """Model for extracted import statements."""

    __tablename__ = "imports"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    module: Mapped[str | None] = mapped_column(String(500))
    alias: Mapped[str | None] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_wildcard: Mapped[bool] = mapped_column(Boolean, default=False)

    __mapper_args__ = {
        "polymorphic_identity": "import",
    }

    def __repr__(self) -> str:
        return f"<Import(id={self.id}, module={self.module}, name={self.name})>"


class Export(ASTNode):
    """Model for extracted export statements."""

    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    exported_type: Mapped[str | None] = mapped_column(String(100))

    __mapper_args__ = {
        "polymorphic_identity": "export",
    }

    def __repr__(self) -> str:
        return f"<Export(id={self.id}, name={self.name})>"


class Variable(ASTNode):
    """Model for extracted variable/constant declarations."""

    __tablename__ = "variables"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    var_type: Mapped[str | None] = mapped_column(String(500))
    is_constant: Mapped[bool] = mapped_column(Boolean, default=False)
    scope: Mapped[str | None] = mapped_column(String(50))
    initial_value: Mapped[str | None] = mapped_column(Text)

    __mapper_args__ = {
        "polymorphic_identity": "variable",
    }

    def __repr__(self) -> str:
        return f"<Variable(id={self.id}, name={self.name}, const={self.is_constant})>"


class Comment(ASTNode):
    """Model for extracted comments and docstrings."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, ForeignKey("ast_nodes.id", ondelete="CASCADE"), primary_key=True)
    text: Mapped[str | None] = mapped_column(Text)
    comment_type: Mapped[str | None] = mapped_column(String(50))
    is_docstring: Mapped[bool] = mapped_column(Boolean, default=False)

    __mapper_args__ = {
        "polymorphic_identity": "comment",
    }

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, type={self.comment_type})>"


class FileParseStatus(Base, TimestampMixin):
    """Model tracking parsing status of each file per parser run for incremental parsing."""

    __tablename__ = "file_parse_statuses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    parser_run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("parser_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, parsed, skipped, failed
    checksum: Mapped[str | None] = mapped_column(String(64))  # SHA256 checksum
    previous_checksum: Mapped[str | None] = mapped_column(String(64))  # Previous checksum for comparison
    parsed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    nodes_extracted: Mapped[int] = mapped_column(Integer, default=0)

    parser_run: Mapped["ParserRun"] = relationship("ParserRun", back_populates="file_parse_statuses")

    __table_args__ = (
        # Unique constraint on parser_run_id and file_id to track each file once per run
        {"schema": None},
    )

    def __repr__(self) -> str:
        return f"<FileParseStatus(id={self.id}, file_id={self.file_id}, status={self.status}, checksum={self.checksum})>"

from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class GitCommit(Base, TimestampMixin):
    """Model representing a single Git commit."""

    __tablename__ = "git_commits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commit_hash: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    parent_hash: Mapped[str | None] = mapped_column(String(40))
    author_name: Mapped[str | None] = mapped_column(String(255))
    author_email: Mapped[str | None] = mapped_column(String(255))
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message: Mapped[str | None] = mapped_column(Text)
    branch: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[str | None] = mapped_column(Text)  # comma-separated

    snapshots: Mapped[list["RepositorySnapshot"]] = relationship(
        "RepositorySnapshot", back_populates="commit", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<GitCommit(id={self.id}, hash={self.commit_hash[:8]})>"


class RepositorySnapshot(Base, TimestampMixin):
    """Model representing a point-in-time snapshot of a repository."""

    __tablename__ = "repository_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    commit_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("git_commits.id", ondelete="SET NULL"), index=True
    )
    parser_run_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("parser_runs.id", ondelete="SET NULL"), index=True
    )
    commit_hash: Mapped[str | None] = mapped_column(String(40))
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_classes: Mapped[int] = mapped_column(Integer, default=0)
    total_functions: Mapped[int] = mapped_column(Integer, default=0)
    total_methods: Mapped[int] = mapped_column(Integer, default=0)
    total_imports: Mapped[int] = mapped_column(Integer, default=0)
    total_variables: Mapped[int] = mapped_column(Integer, default=0)
    snapshot_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    commit: Mapped["GitCommit | None"] = relationship("GitCommit", back_populates="snapshots")
    change_sets: Mapped[list["ChangeSet"]] = relationship(
        "ChangeSet", back_populates="snapshot", cascade="all, delete-orphan",
        foreign_keys="ChangeSet.snapshot_id",
    )

    def __repr__(self) -> str:
        return f"<RepositorySnapshot(id={self.id}, repo_id={self.repository_id}, commit={self.commit_hash})>"


class EntityVersion(Base, TimestampMixin):
    """Model tracking versioned code entities across commits."""

    __tablename__ = "entity_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # class, function, method, variable, import, export
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    start_line: Mapped[int | None] = mapped_column(Integer)
    end_line: Mapped[int | None] = mapped_column(Integer)
    checksum: Mapped[str | None] = mapped_column(String(64))  # SHA256 of entity content
    signature: Mapped[str | None] = mapped_column(Text)  # function signature, class bases, etc.
    change_type: Mapped[str] = mapped_column(String(50), nullable=False, default="created")  # created, modified, deleted, renamed, moved
    previous_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("entity_versions.id", ondelete="SET NULL")
    )

    def __repr__(self) -> str:
        return f"<EntityVersion(id={self.id}, type={self.entity_type}, name={self.entity_name}, change={self.change_type})>"


class ChangeSet(Base, TimestampMixin):
    """Model representing a set of changes between two snapshots."""

    __tablename__ = "change_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    snapshot_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_snapshot_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("repository_snapshots.id", ondelete="SET NULL")
    )
    commit_hash: Mapped[str | None] = mapped_column(String(40))
    total_file_changes: Mapped[int] = mapped_column(Integer, default=0)
    total_entity_changes: Mapped[int] = mapped_column(Integer, default=0)
    files_added: Mapped[int] = mapped_column(Integer, default=0)
    files_modified: Mapped[int] = mapped_column(Integer, default=0)
    files_deleted: Mapped[int] = mapped_column(Integer, default=0)
    files_renamed: Mapped[int] = mapped_column(Integer, default=0)
    entities_added: Mapped[int] = mapped_column(Integer, default=0)
    entities_modified: Mapped[int] = mapped_column(Integer, default=0)
    entities_deleted: Mapped[int] = mapped_column(Integer, default=0)

    snapshot: Mapped["RepositorySnapshot"] = relationship(
        "RepositorySnapshot", back_populates="change_sets", foreign_keys=[snapshot_id]
    )
    file_changes: Mapped[list["FileChange"]] = relationship(
        "FileChange", back_populates="change_set", cascade="all, delete-orphan"
    )
    entity_changes: Mapped[list["EntityChange"]] = relationship(
        "EntityChange", back_populates="change_set", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ChangeSet(id={self.id}, files={self.total_file_changes}, entities={self.total_entity_changes})>"


class FileChange(Base, TimestampMixin):
    """Model representing a single file change between snapshots."""

    __tablename__ = "file_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    change_set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("change_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    previous_path: Mapped[str | None] = mapped_column(String(1000))  # for renames
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # added, modified, deleted, renamed
    language: Mapped[str | None] = mapped_column(String(100))
    previous_checksum: Mapped[str | None] = mapped_column(String(64))
    current_checksum: Mapped[str | None] = mapped_column(String(64))

    change_set: Mapped["ChangeSet"] = relationship("ChangeSet", back_populates="file_changes")

    def __repr__(self) -> str:
        return f"<FileChange(id={self.id}, path={self.file_path}, type={self.change_type})>"


class EntityChange(Base, TimestampMixin):
    """Model representing a single code entity change between snapshots."""

    __tablename__ = "entity_changes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    change_set_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("change_sets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # class, function, method, variable, import, export
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)  # added, modified, deleted, renamed, moved
    previous_name: Mapped[str | None] = mapped_column(String(500))
    previous_file_path: Mapped[str | None] = mapped_column(String(1000))
    details: Mapped[str | None] = mapped_column(Text)  # JSON details of change

    change_set: Mapped["ChangeSet"] = relationship("ChangeSet", back_populates="entity_changes")

    def __repr__(self) -> str:
        return f"<EntityChange(id={self.id}, type={self.entity_type}, name={self.entity_name}, change={self.change_type})>"

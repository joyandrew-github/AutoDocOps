from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Float, Text, DateTime, ForeignKey, BigInteger, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Repository(Base, TimestampMixin):
    """Repository model representing a connected Git repository."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), unique=True, nullable=False, index=True)
    local_path: Mapped[str] = mapped_column(String(500), nullable=False)
    default_branch: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    scans: Mapped[list["RepositoryScan"]] = relationship(
        "RepositoryScan", back_populates="repository", cascade="all, delete-orphan"
    )
    files: Mapped[list["RepositoryFile"]] = relationship(
        "RepositoryFile", back_populates="repository", cascade="all, delete-orphan"
    )
    frameworks: Mapped[list["Framework"]] = relationship(
        "Framework", back_populates="repository", cascade="all, delete-orphan"
    )
    dependencies: Mapped[list["Dependency"]] = relationship(
        "Dependency", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Repository(id={self.id}, name={self.name}, url={self.url})>"


class RepositoryScan(Base, TimestampMixin):
    """Model representing a single scan run of a repository."""

    __tablename__ = "repository_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    languages_detected: Mapped[int] = mapped_column(Integer, default=0)
    frameworks_detected: Mapped[int] = mapped_column(Integer, default=0)
    dependencies_detected: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    repository: Mapped["Repository"] = relationship("Repository", back_populates="scans")

    def __repr__(self) -> str:
        return f"<RepositoryScan(id={self.id}, repo_id={self.repository_id}, status={self.status})>"


class RepositoryFile(Base, TimestampMixin):
    """Model representing a single file found in a repository."""

    __tablename__ = "repository_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    absolute_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(50))
    language: Mapped[str | None] = mapped_column(String(100), index=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    last_modified: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sha256_checksum: Mapped[str | None] = mapped_column(String(64))

    repository: Mapped["Repository"] = relationship("Repository", back_populates="files")

    def __repr__(self) -> str:
        return f"<RepositoryFile(id={self.id}, path={self.relative_path})>"


class ProgrammingLanguage(Base, TimestampMixin):
    """Model for aggregated language statistics per scan."""

    __tablename__ = "programming_languages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)

    def __repr__(self) -> str:
        return f"<ProgrammingLanguage(name={self.name}, files={self.file_count})>"


class Framework(Base, TimestampMixin):
    """Model for detected frameworks in a repository."""

    __tablename__ = "frameworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    confidence: Mapped[str] = mapped_column(String(20), default="high")
    detected_by: Mapped[str | None] = mapped_column(String(255))

    repository: Mapped["Repository"] = relationship("Repository", back_populates="frameworks")

    def __repr__(self) -> str:
        return f"<Framework(name={self.name}, version={self.version})>"


class Dependency(Base, TimestampMixin):
    """Model for detected dependencies in a repository."""

    __tablename__ = "dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repository_scans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str | None] = mapped_column(String(100))
    package_manager: Mapped[str] = mapped_column(String(100), nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(500))

    repository: Mapped["Repository"] = relationship("Repository", back_populates="dependencies")

    def __repr__(self) -> str:
        return f"<Dependency(name={self.name}, version={self.version}, pm={self.package_manager})>"

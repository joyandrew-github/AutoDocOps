"""Models for the Intelligent Documentation Engine."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class Documentation(Base, TimestampMixin):
    """Model representing a generated documentation document."""

    __tablename__ = "documentations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(50), index=True)
    entity_name: Mapped[str | None] = mapped_column(String(500))
    file_path: Mapped[str | None] = mapped_column(String(1000))
    content: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    format: Mapped[str] = mapped_column(String(20), default="markdown")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    language: Mapped[str | None] = mapped_column(String(100))

    sections: Mapped[list["DocumentationSection"]] = relationship(
        "DocumentationSection", back_populates="documentation", cascade="all, delete-orphan"
    )
    versions: Mapped[list["DocumentationVersion"]] = relationship(
        "DocumentationVersion", back_populates="documentation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Documentation(id={self.id}, type={self.doc_type}, title={self.title})>"


class DocumentationVersion(Base, TimestampMixin):
    """Model tracking documentation versions over time."""

    __tablename__ = "documentation_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    documentation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documentations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    change_summary: Mapped[str | None] = mapped_column(Text)

    documentation: Mapped["Documentation"] = relationship("Documentation", back_populates="versions")

    def __repr__(self) -> str:
        return f"<DocumentationVersion(id={self.id}, doc_id={self.documentation_id}, v={self.version})>"


class DocumentationSection(Base, TimestampMixin):
    """Model representing a section within a documentation document."""

    __tablename__ = "documentation_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    documentation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documentations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str | None] = mapped_column(Text)
    section_order: Mapped[int] = mapped_column(Integer, default=0)
    section_type: Mapped[str] = mapped_column(String(50), default="content")
    level: Mapped[int] = mapped_column(Integer, default=2)

    documentation: Mapped["Documentation"] = relationship("Documentation", back_populates="sections")

    def __repr__(self) -> str:
        return f"<DocumentationSection(id={self.id}, title={self.title}, order={self.section_order})>"


class DocumentationJob(Base, TimestampMixin):
    """Model tracking documentation generation jobs."""

    __tablename__ = "documentation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    doc_types_requested: Mapped[str | None] = mapped_column(Text)
    total_documents: Mapped[int] = mapped_column(Integer, default=0)
    documents_created: Mapped[int] = mapped_column(Integer, default=0)
    documents_updated: Mapped[int] = mapped_column(Integer, default=0)
    documents_skipped: Mapped[int] = mapped_column(Integer, default=0)
    documents_failed: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<DocumentationJob(id={self.id}, repo_id={self.repository_id}, status={self.status})>"

"""Models for the Architecture Intelligence Engine."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ArchitectureModel(Base, TimestampMixin):
    """Model representing a high-level architecture analysis."""

    __tablename__ = "architecture_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict | None] = mapped_column(JSON)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    diagrams: Mapped[list["ArchitectureDiagram"]] = relationship(
        "ArchitectureDiagram", back_populates="model", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ArchitectureModel(id={self.id}, type={self.model_type}, name={self.name})>"


class ArchitectureDiagram(Base, TimestampMixin):
    """Model representing an exportable diagram."""

    __tablename__ = "architecture_diagrams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("architecture_models.id", ondelete="CASCADE"), nullable=False, index=True
    )
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diagram_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="mermaid")
    content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str | None] = mapped_column(String(64))

    model: Mapped["ArchitectureModel"] = relationship("ArchitectureModel", back_populates="diagrams")

    def __repr__(self) -> str:
        return f"<ArchitectureDiagram(id={self.id}, type={self.diagram_type}, format={self.format})>"


class ArchitectureSnapshot(Base, TimestampMixin):
    """Model tracking architecture generation runs."""

    __tablename__ = "architecture_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    total_models: Mapped[int] = mapped_column(Integer, default=0)
    models_created: Mapped[int] = mapped_column(Integer, default=0)
    models_updated: Mapped[int] = mapped_column(Integer, default=0)
    models_skipped: Mapped[int] = mapped_column(Integer, default=0)
    diagrams_generated: Mapped[int] = mapped_column(Integer, default=0)
    violations_detected: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def __repr__(self) -> str:
        return f"<ArchitectureSnapshot(id={self.id}, repo_id={self.repository_id}, status={self.status})>"


class ArchitectureViolation(Base, TimestampMixin):
    """Model representing detected architecture violations."""

    __tablename__ = "architecture_violations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    violation_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="warning")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    source_entity: Mapped[str | None] = mapped_column(String(500))
    target_entity: Mapped[str | None] = mapped_column(String(500))
    source_file: Mapped[str | None] = mapped_column(String(1000))
    target_file: Mapped[str | None] = mapped_column(String(1000))
    source_layer: Mapped[str | None] = mapped_column(String(100))
    target_layer: Mapped[str | None] = mapped_column(String(100))
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<ArchitectureViolation(id={self.id}, type={self.violation_type}, severity={self.severity})>"

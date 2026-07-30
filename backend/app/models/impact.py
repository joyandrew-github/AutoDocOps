"""Models for the Impact Analysis Engine."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, Boolean, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin


class ImpactAnalysis(Base, TimestampMixin):
    """Model representing a single impact analysis run."""

    __tablename__ = "impact_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    repository_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    commit_hash: Mapped[str | None] = mapped_column(String(64))
    snapshot_id: Mapped[int | None] = mapped_column(Integer)
    total_changes: Mapped[int] = mapped_column(Integer, default=0)
    total_affected: Mapped[int] = mapped_column(Integer, default=0)
    overall_risk_level: Mapped[str] = mapped_column(String(20), default="low")
    overall_risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str | None] = mapped_column(Text)
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    results: Mapped[list["ImpactResult"]] = relationship(
        "ImpactResult", back_populates="analysis", cascade="all, delete-orphan"
    )
    risk_assessment: Mapped["RiskAssessment | None"] = relationship(
        "RiskAssessment", back_populates="analysis", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ImpactAnalysis(id={self.id}, repo_id={self.repository_id}, status={self.status})>"


class ImpactResult(Base, TimestampMixin):
    """Model representing the impact on a single entity."""

    __tablename__ = "impact_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str | None] = mapped_column(String(1000))
    change_type: Mapped[str] = mapped_column(String(50), nullable=False, default="modified")
    impact_type: Mapped[str] = mapped_column(String(50), nullable=False, default="direct")
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    direct_dependents: Mapped[int] = mapped_column(Integer, default=0)
    indirect_dependents: Mapped[int] = mapped_column(Integer, default=0)
    affected_tests: Mapped[str | None] = mapped_column(Text)
    recommendations: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)

    analysis: Mapped["ImpactAnalysis"] = relationship("ImpactAnalysis", back_populates="results")
    relationships: Mapped[list["ImpactRelationship"]] = relationship(
        "ImpactRelationship", back_populates="result", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ImpactResult(id={self.id}, entity={self.entity_name}, risk={self.risk_level})>"


class ImpactRelationship(Base, TimestampMixin):
    """Model representing a dependency relationship in the impact chain."""

    __tablename__ = "impact_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    result_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("impact_results.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_entity: Mapped[str] = mapped_column(String(500), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(500), nullable=False)
    source_file: Mapped[str | None] = mapped_column(String(1000))
    target_file: Mapped[str | None] = mapped_column(String(1000))
    depth: Mapped[int] = mapped_column(Integer, default=1)

    result: Mapped["ImpactResult"] = relationship("ImpactResult", back_populates="relationships")

    def __repr__(self) -> str:
        return f"<ImpactRelationship(id={self.id}, {self.source_entity} -> {self.target_entity})>"


class RiskAssessment(Base, TimestampMixin):
    """Model representing the overall risk assessment for an analysis."""

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    analysis_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("impact_analyses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")
    risk_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    dependency_score: Mapped[float] = mapped_column(Float, default=0.0)
    api_score: Mapped[float] = mapped_column(Float, default=0.0)
    cross_module_score: Mapped[float] = mapped_column(Float, default=0.0)
    circular_dep_score: Mapped[float] = mapped_column(Float, default=0.0)
    change_frequency_score: Mapped[float] = mapped_column(Float, default=0.0)
    architecture_score: Mapped[float] = mapped_column(Float, default=0.0)
    test_recommendations: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    factors: Mapped[dict | None] = mapped_column(JSON)

    analysis: Mapped["ImpactAnalysis"] = relationship("ImpactAnalysis", back_populates="risk_assessment")

    def __repr__(self) -> str:
        return f"<RiskAssessment(id={self.id}, level={self.risk_level}, score={self.risk_score})>"

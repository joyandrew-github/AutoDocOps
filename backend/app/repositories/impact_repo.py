"""Data access layer for the Impact Analysis Engine."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.impact import (
    ImpactAnalysis,
    ImpactResult,
    ImpactRelationship,
    RiskAssessment,
)


class ImpactRepository:
    """Data access layer for impact analysis entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- ImpactAnalysis ---

    def create_analysis(self, **kwargs) -> ImpactAnalysis:
        a = ImpactAnalysis(**kwargs)
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def update_analysis(self, analysis: ImpactAnalysis, **kwargs) -> ImpactAnalysis:
        for key, value in kwargs.items():
            if hasattr(analysis, key):
                setattr(analysis, key, value)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_analysis_by_id(self, analysis_id: int) -> ImpactAnalysis | None:
        return self.db.query(ImpactAnalysis).filter(ImpactAnalysis.id == analysis_id).first()

    def get_analyses_by_repository(self, repository_id: int, limit: int = 20) -> list[ImpactAnalysis]:
        return (
            self.db.query(ImpactAnalysis)
            .filter(ImpactAnalysis.repository_id == repository_id)
            .order_by(desc(ImpactAnalysis.created_at))
            .limit(limit)
            .all()
        )

    def get_latest_analysis(self, repository_id: int) -> ImpactAnalysis | None:
        return (
            self.db.query(ImpactAnalysis)
            .filter(ImpactAnalysis.repository_id == repository_id)
            .order_by(desc(ImpactAnalysis.created_at))
            .first()
        )

    # --- ImpactResult ---

    def create_result(self, **kwargs) -> ImpactResult:
        r = ImpactResult(**kwargs)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def bulk_create_results(self, records: list[dict]) -> list[ImpactResult]:
        results = []
        for rec in records:
            r = ImpactResult(**rec)
            self.db.add(r)
            results.append(r)
        self.db.commit()
        for r in results:
            self.db.refresh(r)
        return results

    def get_results_by_analysis(self, analysis_id: int) -> list[ImpactResult]:
        return (
            self.db.query(ImpactResult)
            .filter(ImpactResult.analysis_id == analysis_id)
            .order_by(desc(ImpactResult.risk_score))
            .all()
        )

    def get_results_by_entity(self, analysis_id: int, entity_type: str | None = None) -> list[ImpactResult]:
        q = self.db.query(ImpactResult).filter(ImpactResult.analysis_id == analysis_id)
        if entity_type:
            q = q.filter(ImpactResult.entity_type == entity_type)
        return q.order_by(desc(ImpactResult.risk_score)).all()

    def get_result_by_entity_name(self, analysis_id: int, entity_name: str) -> ImpactResult | None:
        return (
            self.db.query(ImpactResult)
            .filter(ImpactResult.analysis_id == analysis_id, ImpactResult.entity_name == entity_name)
            .first()
        )

    # --- ImpactRelationship ---

    def create_relationship(self, **kwargs) -> ImpactRelationship:
        r = ImpactRelationship(**kwargs)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def bulk_create_relationships(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(ImpactRelationship(**rec))
        self.db.commit()

    def get_relationships_by_result(self, result_id: int) -> list[ImpactRelationship]:
        return (
            self.db.query(ImpactRelationship)
            .filter(ImpactRelationship.result_id == result_id)
            .order_by(ImpactRelationship.depth)
            .all()
        )

    # --- RiskAssessment ---

    def create_risk_assessment(self, **kwargs) -> RiskAssessment:
        r = RiskAssessment(**kwargs)
        self.db.add(r)
        self.db.commit()
        self.db.refresh(r)
        return r

    def get_risk_assessment(self, analysis_id: int) -> RiskAssessment | None:
        return (
            self.db.query(RiskAssessment)
            .filter(RiskAssessment.analysis_id == analysis_id)
            .first()
        )

    def get_risk_history(self, repository_id: int, limit: int = 20) -> list[RiskAssessment]:
        return (
            self.db.query(RiskAssessment)
            .join(ImpactAnalysis, RiskAssessment.analysis_id == ImpactAnalysis.id)
            .filter(ImpactAnalysis.repository_id == repository_id)
            .order_by(desc(RiskAssessment.created_at))
            .limit(limit)
            .all()
        )

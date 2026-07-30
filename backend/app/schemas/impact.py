"""Pydantic schemas for the Impact Analysis Engine."""
from datetime import datetime
from typing import Any
from pydantic import BaseModel


class ImpactAnalyzeResponse(BaseModel):
    repository_id: int
    total_changes: int = 0
    total_affected: int = 0
    overall_risk_level: str = "low"
    overall_risk_score: float = 0.0
    duration_seconds: float | None = None
    errors: list[str] = []


class ImpactRelationshipDetail(BaseModel):
    id: int
    relationship_type: str
    source_entity: str
    target_entity: str
    source_file: str | None = None
    target_file: str | None = None
    depth: int = 1

    class Config:
        from_attributes = True


class ImpactResultDetail(BaseModel):
    id: int
    entity_type: str
    entity_name: str
    file_path: str | None = None
    change_type: str = "modified"
    impact_type: str = "direct"
    risk_level: str = "low"
    risk_score: float = 0.0
    direct_dependents: int = 0
    indirect_dependents: int = 0
    affected_tests: str | None = None
    recommendations: str | None = None
    details: Any | None = None

    class Config:
        from_attributes = True


class RiskAssessmentDetail(BaseModel):
    id: int
    risk_level: str = "low"
    risk_score: float = 0.0
    dependency_score: float = 0.0
    api_score: float = 0.0
    cross_module_score: float = 0.0
    circular_dep_score: float = 0.0
    change_frequency_score: float = 0.0
    architecture_score: float = 0.0
    test_recommendations: str | None = None
    summary: str | None = None
    factors: Any | None = None

    class Config:
        from_attributes = True


class ImpactAnalysisDetail(BaseModel):
    id: int
    repository_id: int
    status: str
    trigger_type: str = "manual"
    commit_hash: str | None = None
    total_changes: int = 0
    total_affected: int = 0
    overall_risk_level: str = "low"
    overall_risk_score: float = 0.0
    summary: str | None = None
    duration_seconds: float | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    results: list[ImpactResultDetail] = []
    risk_assessment: RiskAssessmentDetail | None = None

    class Config:
        from_attributes = True


class ImpactAnalysisListItem(BaseModel):
    id: int
    repository_id: int
    status: str
    total_changes: int = 0
    total_affected: int = 0
    overall_risk_level: str = "low"
    overall_risk_score: float = 0.0
    duration_seconds: float | None = None
    created_at: datetime | None = None

    class Config:
        from_attributes = True


class ImpactExportRequest(BaseModel):
    format: str = "json"


class ImpactExportResponse(BaseModel):
    content: str
    format: str

"""API endpoints for the Impact Analysis Engine."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.impact_engine.impact_service import ImpactAnalysisService
from app.schemas.impact import (
    ImpactAnalyzeResponse,
    ImpactAnalysisDetail,
    ImpactAnalysisListItem,
    ImpactResultDetail,
    RiskAssessmentDetail,
    ImpactExportRequest,
    ImpactExportResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> ImpactAnalysisService:
    return ImpactAnalysisService(db)


@router.post(
    "/repositories/{repository_id}/impact/analyze",
    response_model=ImpactAnalyzeResponse,
    summary="Analyze impact",
    description="Run impact analysis for the latest changes in a repository.",
)
def analyze_impact(
    repository_id: int,
    commit_hash: str | None = None,
    service: ImpactAnalysisService = Depends(_get_service),
):
    try:
        stats = service.analyze_impact(repository_id, commit_hash)
        return ImpactAnalyzeResponse(repository_id=repository_id, **stats)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Impact analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during impact analysis.",
        )


@router.get(
    "/impact/{analysis_id}",
    response_model=ImpactAnalysisDetail,
    summary="Get impact analysis",
    description="Get a specific impact analysis with results and risk assessment.",
)
def get_impact_analysis(
    analysis_id: int,
    service: ImpactAnalysisService = Depends(_get_service),
):
    analysis = service.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact analysis not found")
    return ImpactAnalysisDetail(
        id=analysis.id, repository_id=analysis.repository_id, status=analysis.status,
        trigger_type=analysis.trigger_type, commit_hash=analysis.commit_hash,
        total_changes=analysis.total_changes, total_affected=analysis.total_affected,
        overall_risk_level=analysis.overall_risk_level, overall_risk_score=analysis.overall_risk_score,
        summary=analysis.summary, duration_seconds=analysis.duration_seconds,
        created_at=analysis.created_at, completed_at=analysis.completed_at,
        results=[
            ImpactResultDetail(
                id=r.id, entity_type=r.entity_type, entity_name=r.entity_name,
                file_path=r.file_path, change_type=r.change_type, impact_type=r.impact_type,
                risk_level=r.risk_level, risk_score=r.risk_score,
                direct_dependents=r.direct_dependents, indirect_dependents=r.indirect_dependents,
                recommendations=r.recommendations, details=r.details,
            )
            for r in analysis.results
        ],
        risk_assessment=RiskAssessmentDetail(
            id=analysis.risk_assessment.id,
            risk_level=analysis.risk_assessment.risk_level,
            risk_score=analysis.risk_assessment.risk_score,
            dependency_score=analysis.risk_assessment.dependency_score,
            api_score=analysis.risk_assessment.api_score,
            cross_module_score=analysis.risk_assessment.cross_module_score,
            circular_dep_score=analysis.risk_assessment.circular_dep_score,
            change_frequency_score=analysis.risk_assessment.change_frequency_score,
            architecture_score=analysis.risk_assessment.architecture_score,
            test_recommendations=analysis.risk_assessment.test_recommendations,
            summary=analysis.risk_assessment.summary,
            factors=analysis.risk_assessment.factors,
        ) if analysis.risk_assessment else None,
    )


@router.get(
    "/repositories/{repository_id}/impact/history",
    response_model=list[ImpactAnalysisListItem],
    summary="Impact analysis history",
    description="Get recent impact analysis history for a repository.",
)
def get_impact_history(
    repository_id: int,
    limit: int = 20,
    service: ImpactAnalysisService = Depends(_get_service),
):
    analyses = service.get_analysis_history(repository_id, limit)
    return [
        ImpactAnalysisListItem(
            id=a.id, repository_id=a.repository_id, status=a.status,
            total_changes=a.total_changes, total_affected=a.total_affected,
            overall_risk_level=a.overall_risk_level, overall_risk_score=a.overall_risk_score,
            duration_seconds=a.duration_seconds, created_at=a.created_at,
        )
        for a in analyses
    ]


@router.get(
    "/repositories/{repository_id}/impact/entity/{entity_name}",
    response_model=ImpactResultDetail | None,
    summary="Get entity impact",
    description="Get the impact result for a specific entity from the latest analysis.",
)
def get_entity_impact(
    repository_id: int,
    entity_name: str,
    service: ImpactAnalysisService = Depends(_get_service),
):
    result = service.get_entity_impact(repository_id, entity_name)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entity impact not found")
    return ImpactResultDetail(
        id=result.id, entity_type=result.entity_type, entity_name=result.entity_name,
        file_path=result.file_path, change_type=result.change_type, impact_type=result.impact_type,
        risk_level=result.risk_level, risk_score=result.risk_score,
        direct_dependents=result.direct_dependents, indirect_dependents=result.indirect_dependents,
        recommendations=result.recommendations, details=result.details,
    )


@router.get(
    "/repositories/{repository_id}/impact/risk",
    response_model=RiskAssessmentDetail | None,
    summary="Get risk assessment",
    description="Get the risk assessment from the latest impact analysis.",
)
def get_risk_assessment(
    repository_id: int,
    service: ImpactAnalysisService = Depends(_get_service),
):
    risk = service.get_risk_assessment(repository_id)
    if not risk:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No risk assessment found")
    return RiskAssessmentDetail(
        id=risk.id, risk_level=risk.risk_level, risk_score=risk.risk_score,
        dependency_score=risk.dependency_score, api_score=risk.api_score,
        cross_module_score=risk.cross_module_score, circular_dep_score=risk.circular_dep_score,
        change_frequency_score=risk.change_frequency_score, architecture_score=risk.architecture_score,
        test_recommendations=risk.test_recommendations, summary=risk.summary, factors=risk.factors,
    )


@router.post(
    "/impact/{analysis_id}/export",
    response_model=ImpactExportResponse,
    summary="Export impact analysis",
    description="Export an impact analysis in JSON, Markdown, or HTML format.",
)
def export_impact(
    analysis_id: int,
    request: ImpactExportRequest | None = None,
    service: ImpactAnalysisService = Depends(_get_service),
):
    fmt = request.format if request else "json"
    content = service.export_analysis(analysis_id, fmt)
    if not content:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impact analysis not found")
    return ImpactExportResponse(content=content, format=fmt)

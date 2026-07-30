"""API endpoints for the Architecture Intelligence Engine."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.architecture_engine.architecture_service import ArchitectureService
from app.schemas.architecture import (
    ArchitectureGenerateResponse,
    ArchitectureModelDetail,
    ArchitectureModelListItem,
    ArchitectureDiagramDetail,
    ArchitectureViolationDetail,
    DependencyGraphResponse,
    CallGraphResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> ArchitectureService:
    return ArchitectureService(db)


@router.post(
    "/repositories/{repository_id}/architecture/generate",
    response_model=ArchitectureGenerateResponse,
    summary="Generate architecture",
    description="Analyze repository and generate architecture models and diagrams.",
)
def generate_architecture(
    repository_id: int,
    service: ArchitectureService = Depends(_get_service),
):
    try:
        stats = service.generate_architecture(repository_id)
        return ArchitectureGenerateResponse(repository_id=repository_id, **stats)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Architecture generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during architecture generation.",
        )


@router.get(
    "/repositories/{repository_id}/architecture",
    response_model=list[ArchitectureModelListItem],
    summary="List architecture models",
    description="List all architecture models for a repository.",
)
def list_architecture(
    repository_id: int,
    service: ArchitectureService = Depends(_get_service),
):
    models = service.get_architecture(repository_id)
    return [
        ArchitectureModelListItem(
            id=m.id, model_type=m.model_type, name=m.name,
            description=m.description, version=m.version, created_at=m.created_at,
        )
        for m in models
    ]


@router.get(
    "/architecture/{model_id}",
    response_model=ArchitectureModelDetail,
    summary="Get architecture model",
    description="Get a specific architecture model with diagrams.",
)
def get_architecture(
    model_id: int,
    service: ArchitectureService = Depends(_get_service),
):
    model = service.get_architecture_by_id(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Architecture model not found")
    return ArchitectureModelDetail(
        id=model.id, repository_id=model.repository_id, model_type=model.model_type,
        name=model.name, description=model.description, data=model.data,
        content_hash=model.content_hash, version=model.version,
        created_at=model.created_at, updated_at=model.updated_at,
        diagrams=[
            ArchitectureDiagramDetail(
                id=d.id, diagram_type=d.diagram_type, title=d.title,
                format=d.format, content=d.content, content_hash=d.content_hash,
            )
            for d in model.diagrams
        ],
    )


@router.get(
    "/repositories/{repository_id}/architecture/dependencies",
    response_model=DependencyGraphResponse,
    summary="Get dependency graph",
    description="Get the module and file dependency graph.",
)
def get_dependencies(
    repository_id: int,
    service: ArchitectureService = Depends(_get_service),
):
    data = service.get_dependencies(repository_id)
    if not data:
        return DependencyGraphResponse()
    return DependencyGraphResponse(**data)


@router.get(
    "/repositories/{repository_id}/architecture/callgraph",
    response_model=CallGraphResponse,
    summary="Get call graph",
    description="Get the function and method call graph.",
)
def get_callgraph(
    repository_id: int,
    service: ArchitectureService = Depends(_get_service),
):
    data = service.get_callgraph(repository_id)
    if not data:
        return CallGraphResponse()
    return CallGraphResponse(**data)


@router.get(
    "/repositories/{repository_id}/architecture/violations",
    response_model=list[ArchitectureViolationDetail],
    summary="Get architecture violations",
    description="Get detected architecture violations such as circular dependencies and layer violations.",
)
def get_violations(
    repository_id: int,
    resolved: bool | None = None,
    service: ArchitectureService = Depends(_get_service),
):
    violations = service.get_violations(repository_id, resolved)
    return [
        ArchitectureViolationDetail(
            id=v.id, repository_id=v.repository_id, violation_type=v.violation_type,
            severity=v.severity, description=v.description,
            source_entity=v.source_entity, target_entity=v.target_entity,
            source_file=v.source_file, target_file=v.target_file,
            source_layer=v.source_layer, target_layer=v.target_layer,
            is_resolved=v.is_resolved, created_at=v.created_at,
        )
        for v in violations
    ]

"""API endpoints for the Intelligent Documentation Engine."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.documentation_engine.documentation_service import DocumentationService
from app.schemas.documentation import (
    DocumentationGenerateRequest,
    DocumentationGenerateResponse,
    DocumentationDetail,
    DocumentationListItem,
    DocumentationSectionDetail,
    DocumentationSearchRequest,
    DocumentationExportRequest,
    DocumentationExportResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_service(db: Session = Depends(get_db)) -> DocumentationService:
    return DocumentationService(db)


@router.post(
    "/repositories/{repository_id}/documentation/generate",
    response_model=DocumentationGenerateResponse,
    summary="Generate documentation",
    description="Generate or update documentation for a repository.",
)
def generate_documentation(
    repository_id: int,
    request: DocumentationGenerateRequest | None = None,
    service: DocumentationService = Depends(_get_service),
):
    try:
        doc_types = request.doc_types if request else None
        stats = service.generate_documentation(repository_id, doc_types)
        return DocumentationGenerateResponse(repository_id=repository_id, **stats)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during documentation generation.",
        )


@router.get(
    "/repositories/{repository_id}/documentation/master",
    response_model=DocumentationDetail,
    summary="Get master project documentation",
    description="Retrieve the unified master project documentation for a repository.",
)
def get_master_documentation(
    repository_id: int,
    service: DocumentationService = Depends(_get_service),
):
    doc = service.get_master_documentation(repository_id)
    if not doc:
        # Auto-generate if not yet generated
        service.generate_master_documentation(repository_id)
        doc = service.get_master_documentation(repository_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master documentation not found")

    return DocumentationDetail(
        id=doc.id, repository_id=doc.repository_id, doc_type=doc.doc_type,
        title=doc.title, slug=doc.slug, entity_type=doc.entity_type,
        entity_name=doc.entity_name, file_path=doc.file_path,
        content=doc.content, summary=doc.summary, format=doc.format,
        is_published=doc.is_published, version=doc.version, language=doc.language,
        created_at=doc.created_at, updated_at=doc.updated_at,
        sections=[
            DocumentationSectionDetail(
                id=s.id, title=s.title, content=s.content,
                section_order=s.section_order, section_type=s.section_type, level=s.level,
            )
            for s in doc.sections
        ],
    )


@router.get(
    "/repositories/{repository_id}/documentation/master/export",
    summary="Export master project documentation",
    description="Export the master project documentation as printable HTML (PDF ready) or raw Markdown.",
)
def export_master_documentation_endpoint(
    repository_id: int,
    format: str = "markdown",
    service: DocumentationService = Depends(_get_service),
):
    exported = service.export_master_documentation(repository_id, format)
    if not exported:
        service.generate_master_documentation(repository_id)
        exported = service.export_master_documentation(repository_id, format)
    if not exported:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Master documentation not available for export")

    if format in ["html", "pdf"]:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=exported["content"])
    else:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=exported["content"],
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename=\"{exported['filename']}\""},
        )


@router.get(
    "/repositories/{repository_id}/documentation",
    response_model=list[DocumentationListItem],
    summary="List documentation",
    description="List all documentation for a repository, optionally filtered by type.",
)
def list_documentation(
    repository_id: int,
    doc_type: str | None = None,
    service: DocumentationService = Depends(_get_service),
):
    docs = service.get_documentation(repository_id, doc_type)
    return [
        DocumentationListItem(
            id=d.id, doc_type=d.doc_type, title=d.title, slug=d.slug,
            entity_type=d.entity_type, entity_name=d.entity_name,
            file_path=d.file_path, content=d.content, summary=d.summary, version=d.version,
            language=d.language, created_at=d.created_at,
        )
        for d in docs
    ]


@router.get(
    "/documentation/{doc_id}",
    response_model=DocumentationDetail,
    summary="Get documentation",
    description="Get a specific documentation document with sections.",
)
def get_documentation(
    doc_id: int,
    service: DocumentationService = Depends(_get_service),
):
    doc = service.get_documentation_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")
    return DocumentationDetail(
        id=doc.id, repository_id=doc.repository_id, doc_type=doc.doc_type,
        title=doc.title, slug=doc.slug, entity_type=doc.entity_type,
        entity_name=doc.entity_name, file_path=doc.file_path,
        content=doc.content, summary=doc.summary, format=doc.format,
        is_published=doc.is_published, version=doc.version, language=doc.language,
        created_at=doc.created_at, updated_at=doc.updated_at,
        sections=[
            DocumentationSectionDetail(
                id=s.id, title=s.title, content=s.content,
                section_order=s.section_order, section_type=s.section_type, level=s.level,
            )
            for s in doc.sections
        ],
    )


@router.get(
    "/documentation/search",
    response_model=list[DocumentationListItem],
    summary="Search documentation",
    description="Search documentation by query string.",
)
def search_documentation(
    query: str,
    repository_id: int,
    limit: int = 20,
    service: DocumentationService = Depends(_get_service),
):
    docs = service.search_documentation(repository_id, query)
    return [
        DocumentationListItem(
            id=d.id, doc_type=d.doc_type, title=d.title, slug=d.slug,
            entity_type=d.entity_type, entity_name=d.entity_name,
            file_path=d.file_path, summary=d.summary, version=d.version,
            language=d.language, created_at=d.created_at,
        )
        for d in docs[:limit]
    ]


@router.post(
    "/documentation/export",
    response_model=list[DocumentationExportResponse],
    summary="Export documentation",
    description="Export documentation in markdown, HTML, or PDF-ready format.",
)
def export_documentation(
    request: DocumentationExportRequest,
    service: DocumentationService = Depends(_get_service),
):
    if request.doc_id:
        content = service.export_documentation(request.doc_id, request.format)
        if not content:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documentation not found")
        doc = service.get_documentation_by_id(request.doc_id)
        return [DocumentationExportResponse(
            title=doc.title, doc_type=doc.doc_type, content=content, format=request.format,
        )]
    elif request.repository_id:
        results = service.export_all(request.repository_id, request.format)
        return [
            DocumentationExportResponse(
                title=r["title"], doc_type=r["doc_type"], content=r["content"], format=r["format"],
            )
            for r in results
        ]
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide doc_id or repository_id")

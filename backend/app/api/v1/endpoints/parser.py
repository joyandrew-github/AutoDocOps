from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.parser_engine.parser_service import ParserService
from app.repositories.repository_repo import RepositoryRepository
from app.schemas.parser import (
    ParserRunResponse,
    ParseRequestResponse,
    ASTSummaryResponse,
    FunctionResponse,
    ClassResponse,
    ImportResponse,
    VariableResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_parser_service(db: Session = Depends(get_db)) -> ParserService:
    return ParserService(db)


def _get_repo(db: Session = Depends(get_db)) -> RepositoryRepository:
    return RepositoryRepository(db)


def _validate_repository(repository_id: int, repo: RepositoryRepository):
    repository = repo.get_repository_by_id(repository_id)
    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository not found: {repository_id}",
        )
    return repository


@router.post(
    "/repositories/{repository_id}/parse",
    response_model=ParseRequestResponse,
    summary="Parse a repository",
    description="Parse all supported source files in a repository using Tree-sitter to extract AST nodes.",
)
def parse_repository(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    _validate_repository(repository_id, repo)

    service = ParserService(db)
    try:
        run = service.parse_repository(repository_id)

        # Automatically update repository-specific knowledge graph
        try:
            from app.db.neo4j import get_neo4j_client
            from app.engines.graph_engine.graph_sync_service import GraphSyncService
            GraphSyncService(db, get_neo4j_client()).sync_repository(repository_id)
        except Exception as ge:
            logger.warning(f"Auto graph sync after parse for repository {repository_id}: {ge}")

        return ParseRequestResponse(
            parser_run=ParserRunResponse.model_validate(run),
            message=f"Parsing {'completed' if run.status == 'completed' else 'failed'}. "
                    f"{run.total_files_parsed} files parsed, {run.total_nodes_extracted} nodes extracted.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error parsing repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during parsing.",
        )


@router.get(
    "/repositories/{repository_id}/ast",
    response_model=ASTSummaryResponse,
    summary="Get AST summary",
    description="Retrieve a summary of all AST nodes extracted from a repository.",
)
def get_ast_summary(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    _validate_repository(repository_id, repo)

    service = ParserService(db)
    summary = service.get_ast_summary(repository_id)

    if not summary["parser_run"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No parser run found. Parse the repository first.",
        )

    return ASTSummaryResponse(
        parser_run=ParserRunResponse.model_validate(summary["parser_run"]),
        total_functions=summary["total_functions"],
        total_classes=summary["total_classes"],
        total_methods=summary["total_methods"],
        total_imports=summary["total_imports"],
        total_exports=summary["total_exports"],
        total_variables=summary["total_variables"],
        total_comments=summary["total_comments"],
    )


@router.get(
    "/repositories/{repository_id}/functions",
    response_model=list[FunctionResponse],
    summary="Get functions",
    description="Retrieve all functions extracted from a repository.",
)
def get_functions(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    _validate_repository(repository_id, repo)
    service = ParserService(db)
    return service.get_functions(repository_id)


@router.get(
    "/repositories/{repository_id}/classes",
    response_model=list[ClassResponse],
    summary="Get classes",
    description="Retrieve all classes extracted from a repository.",
)
def get_classes(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    _validate_repository(repository_id, repo)
    service = ParserService(db)
    return service.get_classes(repository_id)


@router.get(
    "/repositories/{repository_id}/imports",
    response_model=list[ImportResponse],
    summary="Get imports",
    description="Retrieve all import statements extracted from a repository.",
)
def get_imports(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    _validate_repository(repository_id, repo)
    service = ParserService(db)
    return service.get_imports(repository_id)


@router.get(
    "/repositories/{repository_id}/variables",
    response_model=list[VariableResponse],
    summary="Get variables",
    description="Retrieve all variables and constants extracted from a repository.",
)
def get_variables(
    repository_id: int,
    db: Session = Depends(get_db),
):
    repo = RepositoryRepository(db)
    _validate_repository(repository_id, repo)
    service = ParserService(db)
    return service.get_variables(repository_id)

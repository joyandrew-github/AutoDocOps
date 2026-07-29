from datetime import datetime
from pydantic import BaseModel


# --- Response Schemas ---

class ParserRunResponse(BaseModel):
    id: int
    repository_id: int
    status: str
    total_files_parsed: int
    total_nodes_extracted: int
    total_functions: int
    total_classes: int
    total_imports: int
    duration_seconds: float | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    # Incremental parsing fields
    files_parsed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    parser_version: str = "1.0.0"

    model_config = {"from_attributes": True}


class ASTNodeResponse(BaseModel):
    id: int
    file_id: int
    parser_run_id: int
    node_type: str
    name: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    start_column: int | None = None
    end_column: int | None = None

    model_config = {"from_attributes": True}


class FunctionResponse(ASTNodeResponse):
    parameters: str | None = None
    return_type: str | None = None
    decorators: str | None = None
    is_async: bool = False
    is_generator: bool = False
    docstring: str | None = None
    body_start_line: int | None = None
    body_end_line: int | None = None


class ClassResponse(ASTNodeResponse):
    bases: str | None = None
    decorators: str | None = None
    docstring: str | None = None
    is_abstract: bool = False
    interfaces: str | None = None


class MethodResponse(ASTNodeResponse):
    class_name: str | None = None
    parameters: str | None = None
    return_type: str | None = None
    decorators: str | None = None
    is_async: bool = False
    is_static: bool = False
    is_constructor: bool = False
    docstring: str | None = None


class ImportResponse(ASTNodeResponse):
    module: str | None = None
    alias: str | None = None
    is_default: bool = False
    is_wildcard: bool = False


class ExportResponse(ASTNodeResponse):
    is_default: bool = False
    exported_type: str | None = None


class VariableResponse(ASTNodeResponse):
    var_type: str | None = None
    is_constant: bool = False
    scope: str | None = None
    initial_value: str | None = None


class CommentResponse(ASTNodeResponse):
    text: str | None = None
    comment_type: str | None = None
    is_docstring: bool = False


class ASTSummaryResponse(BaseModel):
    parser_run: ParserRunResponse
    total_functions: int
    total_classes: int
    total_methods: int
    total_imports: int
    total_exports: int
    total_variables: int
    total_comments: int


class ParseRequestResponse(BaseModel):
    parser_run: ParserRunResponse
    message: str

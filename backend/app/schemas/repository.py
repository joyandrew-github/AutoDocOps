from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


# --- Request Schemas ---

class RepositoryConnectRequest(BaseModel):
    repository_url: str = Field(
        ..., description="Git repository HTTPS URL", examples=["https://github.com/owner/repo.git"]
    )

    @field_validator("repository_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        pattern = r"^https?://.+/.+$"
        if not re.match(pattern, v):
            raise ValueError("Invalid repository URL. Must be a valid HTTPS Git URL.")
        return v.strip()


# --- Response Schemas ---

class RepositoryResponse(BaseModel):
    id: int
    name: str
    url: str
    local_path: str
    default_branch: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepositoryScanResponse(BaseModel):
    id: int
    repository_id: int
    status: str
    total_files: int
    total_size_bytes: int
    languages_detected: int
    frameworks_detected: int
    dependencies_detected: int
    duration_seconds: float | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RepositoryFileResponse(BaseModel):
    id: int
    repository_id: int
    scan_id: int
    file_name: str
    relative_path: str
    absolute_path: str
    extension: str | None = None
    language: str | None = None
    size_bytes: int
    last_modified: datetime | None = None
    sha256_checksum: str | None = None

    model_config = {"from_attributes": True}


class ProgrammingLanguageResponse(BaseModel):
    id: int
    repository_id: int
    scan_id: int
    name: str
    file_count: int
    total_size_bytes: int
    percentage: float

    model_config = {"from_attributes": True}


class FrameworkResponse(BaseModel):
    id: int
    repository_id: int
    scan_id: int
    name: str
    version: str | None = None
    confidence: str
    detected_by: str | None = None

    model_config = {"from_attributes": True}


class DependencyResponse(BaseModel):
    id: int
    repository_id: int
    scan_id: int
    name: str
    version: str | None = None
    package_manager: str
    source_file: str | None = None

    model_config = {"from_attributes": True}


class RepositoryDetailResponse(RepositoryResponse):
    latest_scan: RepositoryScanResponse | None = None


class ScanSummaryResponse(BaseModel):
    scan: RepositoryScanResponse
    languages: list[ProgrammingLanguageResponse]
    frameworks: list[FrameworkResponse]
    dependencies_count: int
    files_count: int

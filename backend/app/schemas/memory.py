from datetime import datetime
from pydantic import BaseModel


# --- Response Schemas ---

class GitCommitResponse(BaseModel):
    id: int
    repository_id: int
    commit_hash: str
    parent_hash: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    committed_at: datetime | None = None
    message: str | None = None
    branch: str | None = None
    tags: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RepositorySnapshotResponse(BaseModel):
    id: int
    repository_id: int
    commit_id: int | None = None
    parser_run_id: int | None = None
    commit_hash: str | None = None
    total_files: int = 0
    total_classes: int = 0
    total_functions: int = 0
    total_methods: int = 0
    total_imports: int = 0
    total_variables: int = 0
    snapshot_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class EntityVersionResponse(BaseModel):
    id: int
    repository_id: int
    snapshot_id: int
    entity_type: str
    entity_name: str
    file_path: str
    start_line: int | None = None
    end_line: int | None = None
    checksum: str | None = None
    signature: str | None = None
    change_type: str = "created"
    previous_version_id: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FileChangeResponse(BaseModel):
    id: int
    change_set_id: int
    file_path: str
    previous_path: str | None = None
    change_type: str
    language: str | None = None
    previous_checksum: str | None = None
    current_checksum: str | None = None

    model_config = {"from_attributes": True}


class EntityChangeResponse(BaseModel):
    id: int
    change_set_id: int
    entity_type: str
    entity_name: str
    file_path: str
    change_type: str
    previous_name: str | None = None
    previous_file_path: str | None = None
    details: str | None = None

    model_config = {"from_attributes": True}


class ChangeSetResponse(BaseModel):
    id: int
    repository_id: int
    snapshot_id: int
    previous_snapshot_id: int | None = None
    commit_hash: str | None = None
    total_file_changes: int = 0
    total_entity_changes: int = 0
    files_added: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    files_renamed: int = 0
    entities_added: int = 0
    entities_modified: int = 0
    entities_deleted: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class ChangeSetDetailResponse(ChangeSetResponse):
    file_changes: list[FileChangeResponse] = []
    entity_changes: list[EntityChangeResponse] = []


class TimelineEntryResponse(BaseModel):
    commit: GitCommitResponse | None = None
    snapshot: RepositorySnapshotResponse | None = None
    change_set: ChangeSetResponse | None = None


class TimelineResponse(BaseModel):
    repository_id: int
    total_commits: int
    total_snapshots: int
    entries: list[TimelineEntryResponse]

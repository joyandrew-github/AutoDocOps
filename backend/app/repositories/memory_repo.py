from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.memory import (
    GitCommit,
    RepositorySnapshot,
    EntityVersion,
    ChangeSet,
    FileChange,
    EntityChange,
)


class MemoryRepository:
    """Data access layer for Repository Memory Engine entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- GitCommit ---

    def create_commit(self, **kwargs) -> GitCommit:
        commit = GitCommit(**kwargs)
        self.db.add(commit)
        self.db.commit()
        self.db.refresh(commit)
        return commit

    def bulk_create_commits(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(GitCommit(**rec))
        self.db.commit()

    def get_commit_by_hash(self, repository_id: int, commit_hash: str) -> GitCommit | None:
        return (
            self.db.query(GitCommit)
            .filter(GitCommit.repository_id == repository_id, GitCommit.commit_hash == commit_hash)
            .first()
        )

    def get_commits_by_repository(self, repository_id: int, limit: int = 50) -> list[GitCommit]:
        return (
            self.db.query(GitCommit)
            .filter(GitCommit.repository_id == repository_id)
            .order_by(desc(GitCommit.committed_at))
            .limit(limit)
            .all()
        )

    def get_commit_count(self, repository_id: int) -> int:
        return (
            self.db.query(GitCommit)
            .filter(GitCommit.repository_id == repository_id)
            .count()
        )

    # --- RepositorySnapshot ---

    def create_snapshot(self, **kwargs) -> RepositorySnapshot:
        snapshot = RepositorySnapshot(**kwargs)
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def update_snapshot(self, snapshot: RepositorySnapshot, **kwargs) -> RepositorySnapshot:
        for key, value in kwargs.items():
            if hasattr(snapshot, key):
                setattr(snapshot, key, value)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_latest_snapshot(self, repository_id: int) -> RepositorySnapshot | None:
        return (
            self.db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repository_id)
            .order_by(desc(RepositorySnapshot.snapshot_at))
            .first()
        )

    def get_previous_snapshot(self, repository_id: int, current_snapshot_id: int) -> RepositorySnapshot | None:
        return (
            self.db.query(RepositorySnapshot)
            .filter(
                RepositorySnapshot.repository_id == repository_id,
                RepositorySnapshot.id < current_snapshot_id,
            )
            .order_by(desc(RepositorySnapshot.snapshot_at))
            .first()
        )

    def get_snapshots_by_repository(self, repository_id: int, limit: int = 50) -> list[RepositorySnapshot]:
        return (
            self.db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repository_id)
            .order_by(desc(RepositorySnapshot.snapshot_at))
            .limit(limit)
            .all()
        )

    def get_snapshot_count(self, repository_id: int) -> int:
        return (
            self.db.query(RepositorySnapshot)
            .filter(RepositorySnapshot.repository_id == repository_id)
            .count()
        )

    # --- EntityVersion ---

    def create_entity_version(self, **kwargs) -> EntityVersion:
        ev = EntityVersion(**kwargs)
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    def bulk_create_entity_versions(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(EntityVersion(**rec))
        self.db.commit()

    def get_entity_versions_by_snapshot(self, snapshot_id: int) -> list[EntityVersion]:
        return (
            self.db.query(EntityVersion)
            .filter(EntityVersion.snapshot_id == snapshot_id)
            .order_by(EntityVersion.entity_type, EntityVersion.entity_name)
            .all()
        )

    # --- ChangeSet ---

    def create_change_set(self, **kwargs) -> ChangeSet:
        cs = ChangeSet(**kwargs)
        self.db.add(cs)
        self.db.commit()
        self.db.refresh(cs)
        return cs

    def update_change_set(self, cs: ChangeSet, **kwargs) -> ChangeSet:
        for key, value in kwargs.items():
            if hasattr(cs, key):
                setattr(cs, key, value)
        self.db.commit()
        self.db.refresh(cs)
        return cs

    def get_change_sets_by_repository(self, repository_id: int, limit: int = 50) -> list[ChangeSet]:
        return (
            self.db.query(ChangeSet)
            .filter(ChangeSet.repository_id == repository_id)
            .order_by(desc(ChangeSet.created_at))
            .limit(limit)
            .all()
        )

    def get_change_set_by_commit(self, repository_id: int, commit_hash: str) -> ChangeSet | None:
        return (
            self.db.query(ChangeSet)
            .filter(ChangeSet.repository_id == repository_id, ChangeSet.commit_hash == commit_hash)
            .first()
        )

    # --- FileChange ---

    def bulk_create_file_changes(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(FileChange(**rec))
        self.db.commit()

    def get_file_changes_by_change_set(self, change_set_id: int) -> list[FileChange]:
        return (
            self.db.query(FileChange)
            .filter(FileChange.change_set_id == change_set_id)
            .order_by(FileChange.change_type, FileChange.file_path)
            .all()
        )

    # --- EntityChange ---

    def bulk_create_entity_changes(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(EntityChange(**rec))
        self.db.commit()

    def get_entity_changes_by_change_set(self, change_set_id: int) -> list[EntityChange]:
        return (
            self.db.query(EntityChange)
            .filter(EntityChange.change_set_id == change_set_id)
            .order_by(EntityChange.change_type, EntityChange.entity_type, EntityChange.entity_name)
            .all()
        )

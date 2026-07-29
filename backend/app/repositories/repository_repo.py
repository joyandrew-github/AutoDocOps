from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.repository import (
    Repository,
    RepositoryScan,
    RepositoryFile,
    ProgrammingLanguage,
    Framework,
    Dependency,
)


class RepositoryRepository:
    """Data access layer for Repository entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- Repository ---

    def create_repository(self, name: str, url: str, local_path: str, default_branch: str | None = None) -> Repository:
        repo = Repository(
            name=name,
            url=url,
            local_path=local_path,
            default_branch=default_branch,
        )
        self.db.add(repo)
        self.db.commit()
        self.db.refresh(repo)
        return repo

    def get_repository_by_id(self, repo_id: int) -> Repository | None:
        return self.db.query(Repository).filter(Repository.id == repo_id).first()

    def get_repository_by_url(self, url: str) -> Repository | None:
        return self.db.query(Repository).filter(Repository.url == url).first()

    def get_all_repositories(self) -> list[Repository]:
        return self.db.query(Repository).order_by(desc(Repository.created_at)).all()

    def update_repository(self, repo: Repository, **kwargs) -> Repository:
        for key, value in kwargs.items():
            if hasattr(repo, key):
                setattr(repo, key, value)
        self.db.commit()
        self.db.refresh(repo)
        return repo

    # --- RepositoryScan ---

    def create_scan(self, repository_id: int) -> RepositoryScan:
        scan = RepositoryScan(repository_id=repository_id, status="pending")
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def update_scan(self, scan: RepositoryScan, **kwargs) -> RepositoryScan:
        for key, value in kwargs.items():
            if hasattr(scan, key):
                setattr(scan, key, value)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def get_latest_scan(self, repository_id: int) -> RepositoryScan | None:
        return (
            self.db.query(RepositoryScan)
            .filter(RepositoryScan.repository_id == repository_id)
            .order_by(desc(RepositoryScan.created_at))
            .first()
        )

    # --- RepositoryFile ---

    def bulk_create_files(self, files: list[dict]) -> None:
        self.db.bulk_insert_mappings(RepositoryFile, files)
        self.db.commit()

    def get_files_by_repository(self, repository_id: int) -> list[RepositoryFile]:
        return (
            self.db.query(RepositoryFile)
            .filter(RepositoryFile.repository_id == repository_id)
            .order_by(RepositoryFile.relative_path)
            .all()
        )

    def delete_files_by_repository(self, repository_id: int) -> None:
        self.db.query(RepositoryFile).filter(RepositoryFile.repository_id == repository_id).delete()
        self.db.commit()

    # --- ProgrammingLanguage ---

    def bulk_create_languages(self, languages: list[dict]) -> None:
        self.db.bulk_insert_mappings(ProgrammingLanguage, languages)
        self.db.commit()

    def get_languages_by_repository(self, repository_id: int) -> list[ProgrammingLanguage]:
        return (
            self.db.query(ProgrammingLanguage)
            .filter(ProgrammingLanguage.repository_id == repository_id)
            .order_by(desc(ProgrammingLanguage.percentage))
            .all()
        )

    def delete_languages_by_repository(self, repository_id: int) -> None:
        self.db.query(ProgrammingLanguage).filter(
            ProgrammingLanguage.repository_id == repository_id
        ).delete()
        self.db.commit()

    # --- Framework ---

    def bulk_create_frameworks(self, frameworks: list[dict]) -> None:
        self.db.bulk_insert_mappings(Framework, frameworks)
        self.db.commit()

    def get_frameworks_by_repository(self, repository_id: int) -> list[Framework]:
        return (
            self.db.query(Framework)
            .filter(Framework.repository_id == repository_id)
            .all()
        )

    def delete_frameworks_by_repository(self, repository_id: int) -> None:
        self.db.query(Framework).filter(Framework.repository_id == repository_id).delete()
        self.db.commit()

    # --- Dependency ---

    def bulk_create_dependencies(self, dependencies: list[dict]) -> None:
        self.db.bulk_insert_mappings(Dependency, dependencies)
        self.db.commit()

    def get_dependencies_by_repository(self, repository_id: int) -> list[Dependency]:
        return (
            self.db.query(Dependency)
            .filter(Dependency.repository_id == repository_id)
            .order_by(Dependency.package_manager, Dependency.name)
            .all()
        )

    def delete_dependencies_by_repository(self, repository_id: int) -> None:
        self.db.query(Dependency).filter(Dependency.repository_id == repository_id).delete()
        self.db.commit()

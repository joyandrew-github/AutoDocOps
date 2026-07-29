from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.repository_repo import RepositoryRepository
from app.services.git_manager import GitManager, GitError
from app.services.repository_scanner import RepositoryScanner
from app.models.repository import (
    Repository,
    RepositoryScan,
    RepositoryFile,
    ProgrammingLanguage,
    Framework,
    Dependency,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepositoryService:
    """Orchestrates repository intelligence operations."""

    def __init__(self, db: Session):
        self.repo = RepositoryRepository(db)
        self.git_manager = GitManager()
        self.scanner = RepositoryScanner()

    def connect_repository(self, url: str) -> Repository:
        """Clone or pull a repository and register it in the database."""
        # Check if already connected
        existing = self.repo.get_repository_by_url(url)
        if existing:
            logger.info(f"Repository already connected: {url}, pulling latest")
            local_path, branch = self.git_manager.clone_or_pull(url)
            self.repo.update_repository(
                existing,
                local_path=str(local_path),
                default_branch=branch,
            )
            return existing

        # Clone new
        local_path, branch = self.git_manager.clone_or_pull(url)
        name = self.git_manager.extract_repo_name(url)

        repository = self.repo.create_repository(
            name=name,
            url=url,
            local_path=str(local_path),
            default_branch=branch,
        )
        logger.info(f"Repository connected: {name} (id={repository.id})")
        return repository

    def scan_repository(self, repository_id: int) -> RepositoryScan:
        """Run a full scan on a repository."""
        repository = self.repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        # Create scan record
        scan = self.repo.create_scan(repository_id)
        self.repo.update_scan(
            scan,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
        )

        try:
            # Pull latest changes before scanning
            try:
                self.git_manager.clone_or_pull(repository.url)
            except GitError as e:
                logger.warning(f"Pull failed before scan, proceeding with existing code: {e}")

            # Run scanner
            result = self.scanner.scan(repository.local_path)

            if result.error:
                self.repo.update_scan(
                    scan,
                    status="failed",
                    error_message=result.error,
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=result.duration_seconds,
                )
                return scan

            # Clear old scan data for this repository
            self.repo.delete_files_by_repository(repository_id)
            self.repo.delete_languages_by_repository(repository_id)
            self.repo.delete_frameworks_by_repository(repository_id)
            self.repo.delete_dependencies_by_repository(repository_id)

            # Store files
            file_records = [
                {
                    "repository_id": repository_id,
                    "scan_id": scan.id,
                    "file_name": f.file_name,
                    "relative_path": f.relative_path,
                    "absolute_path": f.absolute_path,
                    "extension": f.extension,
                    "language": f.language,
                    "size_bytes": f.size_bytes,
                    "last_modified": f.last_modified,
                    "sha256_checksum": f.sha256_checksum,
                }
                for f in result.files
            ]
            if file_records:
                self.repo.bulk_create_files(file_records)

            # Store language stats
            lang_records = [
                {
                    "repository_id": repository_id,
                    "scan_id": scan.id,
                    "name": lang_name,
                    "file_count": stats["file_count"],
                    "total_size_bytes": stats["total_size_bytes"],
                    "percentage": stats["percentage"],
                }
                for lang_name, stats in result.language_stats.items()
            ]
            if lang_records:
                self.repo.bulk_create_languages(lang_records)

            # Store frameworks
            fw_records = [
                {
                    "repository_id": repository_id,
                    "scan_id": scan.id,
                    "name": fw.name,
                    "version": fw.version,
                    "confidence": fw.confidence,
                    "detected_by": fw.detected_by,
                }
                for fw in result.frameworks
            ]
            if fw_records:
                self.repo.bulk_create_frameworks(fw_records)

            # Store dependencies
            dep_records = [
                {
                    "repository_id": repository_id,
                    "scan_id": scan.id,
                    "name": dep.name,
                    "version": dep.version,
                    "package_manager": dep.package_manager,
                    "source_file": dep.source_file,
                }
                for dep in result.dependencies
            ]
            if dep_records:
                self.repo.bulk_create_dependencies(dep_records)

            # Update scan with results
            self.repo.update_scan(
                scan,
                status="completed",
                total_files=len(result.files),
                total_size_bytes=result.total_size_bytes,
                languages_detected=len(result.language_stats),
                frameworks_detected=len(result.frameworks),
                dependencies_detected=len(result.dependencies),
                duration_seconds=result.duration_seconds,
                completed_at=datetime.now(timezone.utc),
            )

            logger.info(
                f"Scan completed for repository {repository_id}: "
                f"{len(result.files)} files, "
                f"{len(result.language_stats)} languages, "
                f"{len(result.frameworks)} frameworks, "
                f"{len(result.dependencies)} dependencies "
                f"in {result.duration_seconds}s"
            )

        except Exception as e:
            logger.error(f"Scan failed for repository {repository_id}: {e}")
            self.repo.update_scan(
                scan,
                status="failed",
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )

        return scan

    def get_all_repositories(self) -> list[Repository]:
        return self.repo.get_all_repositories()

    def get_repository(self, repository_id: int) -> Repository | None:
        return self.repo.get_repository_by_id(repository_id)

    def get_repository_files(self, repository_id: int) -> list[RepositoryFile]:
        return self.repo.get_files_by_repository(repository_id)

    def get_repository_dependencies(self, repository_id: int) -> list[Dependency]:
        return self.repo.get_dependencies_by_repository(repository_id)

    def get_repository_frameworks(self, repository_id: int) -> list[Framework]:
        return self.repo.get_frameworks_by_repository(repository_id)

    def get_repository_languages(self, repository_id: int) -> list[ProgrammingLanguage]:
        return self.repo.get_languages_by_repository(repository_id)

    def get_latest_scan(self, repository_id: int) -> RepositoryScan | None:
        return self.repo.get_latest_scan(repository_id)

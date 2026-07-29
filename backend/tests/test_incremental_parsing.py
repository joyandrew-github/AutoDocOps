"""Unit tests for incremental parsing with SHA256 checksums."""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.parser import ParserRun, FileParseStatus
from app.models.repository import Repository, RepositoryFile
from app.repositories.parser_repo import ParserRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class TestIncrementalParsing:
    """Test incremental parsing functionality."""

    @pytest.fixture
    def db(self):
        """Create a test database session."""
        from app.db.session import SessionLocal
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    @pytest.fixture
    def parser_repo(self, db):
        """Create parser repository."""
        return ParserRepository(db)

    @pytest.fixture
    def repository(self, db):
        """Create a test repository."""
        repo = Repository(
            name="test-repo",
            url="https://github.com/test/repo.git",
            local_path="/tmp/test-repo",
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        return repo

    @pytest.fixture
    def test_files(self, db, repository):
        """Create test repository files with checksums."""
        files = [
            RepositoryFile(
                repository_id=repository.id,
                relative_path="file1.py",
                absolute_path="/tmp/test-repo/file1.py",
                extension=".py",
                language="Python",
                size_bytes=100,
                checksum="abc123",
            ),
            RepositoryFile(
                repository_id=repository.id,
                relative_path="file2.py",
                absolute_path="/tmp/test-repo/file2.py",
                extension=".py",
                language="Python",
                size_bytes=200,
                checksum="def456",
            ),
        ]
        for f in files:
            db.add(f)
        db.commit()
        return files

    def test_get_latest_completed_parser_run(self, db, parser_repo, repository):
        """Test getting the latest completed parser run."""
        # Create multiple parser runs
        run1 = parser_repo.create_parser_run(repository.id)
        parser_repo.update_parser_run(run1, status="completed", completed_at=datetime.now(timezone.utc))

        run2 = parser_repo.create_parser_run(repository.id)
        parser_repo.update_parser_run(run2, status="failed", completed_at=datetime.now(timezone.utc))

        run3 = parser_repo.create_parser_run(repository.id)
        parser_repo.update_parser_run(run3, status="completed", completed_at=datetime.now(timezone.utc))

        # Get latest completed run
        latest_completed = parser_repo.get_latest_completed_parser_run(repository.id)

        assert latest_completed is not None
        assert latest_completed.id == run3.id
        assert latest_completed.status == "completed"

    def test_get_file_checksums_by_parser_run(self, db, parser_repo, repository, test_files):
        """Test getting file checksums by parser run."""
        # Create parser run
        run = parser_repo.create_parser_run(repository.id)

        # Create file parse statuses
        for f in test_files:
            parser_repo.create_file_parse_status(
                parser_run_id=run.id,
                file_id=f.id,
                status="parsed",
                checksum=f.checksum,
            )

        # Get checksums
        checksums = parser_repo.get_file_checksums_by_parser_run(run.id)

        assert len(checksums) == len(test_files)
        assert checksums[test_files[0].id] == test_files[0].checksum
        assert checksums[test_files[1].id] == test_files[1].checksum

    def test_file_parse_status_skipped(self, db, parser_repo, repository, test_files):
        """Test creating a skipped file parse status."""
        run = parser_repo.create_parser_run(repository.id)

        status = parser_repo.create_file_parse_status(
            parser_run_id=run.id,
            file_id=test_files[0].id,
            status="skipped",
            checksum=test_files[0].checksum,
            previous_checksum="old_checksum",
        )

        assert status.status == "skipped"
        assert status.checksum == test_files[0].checksum
        assert status.previous_checksum == "old_checksum"

    def test_file_parse_status_failed(self, db, parser_repo, repository, test_files):
        """Test creating a failed file parse status."""
        run = parser_repo.create_parser_run(repository.id)

        status = parser_repo.create_file_parse_status(
            parser_run_id=run.id,
            file_id=test_files[0].id,
            status="failed",
            checksum=test_files[0].checksum,
            error_message="Syntax error",
        )

        assert status.status == "failed"
        assert status.error_message == "Syntax error"

    def test_file_parse_status_parsed(self, db, parser_repo, repository, test_files):
        """Test creating a parsed file parse status."""
        run = parser_repo.create_parser_run(repository.id)

        status = parser_repo.create_file_parse_status(
            parser_run_id=run.id,
            file_id=test_files[0].id,
            status="parsed",
            checksum=test_files[0].checksum,
            previous_checksum="old_checksum",
            nodes_extracted=5,
            parsed_at=datetime.now(timezone.utc),
        )

        assert status.status == "parsed"
        assert status.checksum == test_files[0].checksum
        assert status.previous_checksum == "old_checksum"
        assert status.nodes_extracted == 5
        assert status.parsed_at is not None

    def test_parser_run_has_incremental_fields(self, db, parser_repo, repository):
        """Test that parser run includes incremental parsing fields."""
        run = parser_repo.create_parser_run(repository.id)

        parser_repo.update_parser_run(
            run,
            status="completed",
            files_parsed=5,
            files_skipped=10,
            files_failed=2,
            parser_version="1.0.0",
        )

        db.refresh(run)
        assert run.files_parsed == 5
        assert run.files_skipped == 10
        assert run.files_failed == 2
        assert run.parser_version == "1.0.0"

    def test_delete_nodes_by_file_and_run(self, db, parser_repo, repository, test_files):
        """Test deleting AST nodes by file and parser run."""
        run = parser_repo.create_parser_run(repository.id)

        # This should not raise an error even if no nodes exist
        parser_repo.delete_nodes_by_file_and_run(test_files[0].id, run.id)

    def test_incremental_parsing_checksum_comparison(self, db, parser_repo, repository, test_files):
        """Test checksum comparison logic for incremental parsing."""
        # Create first parser run with checksums
        run1 = parser_repo.create_parser_run(repository.id)
        for f in test_files:
            parser_repo.create_file_parse_status(
                parser_run_id=run1.id,
                file_id=f.id,
                status="parsed",
                checksum=f.checksum,
            )

        # Get checksums from first run
        checksums = parser_repo.get_file_checksums_by_parser_run(run1.id)

        # Simulate file modification
        test_files[0].checksum = "new_checksum_123"
        db.commit()

        # Checksums should differ
        assert checksums[test_files[0].id] != test_files[0].checksum
        assert checksums[test_files[1].id] == test_files[1].checksum

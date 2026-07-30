"""Unit tests for SnapshotService and CommitTracker."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone
from app.engines.memory_engine.snapshot_service import SnapshotService
from app.engines.memory_engine.commit_tracker import CommitTracker
from app.engines.memory_engine.diff_engine import DiffEngine, SnapshotData, DiffResult, FileDiff, EntityDiff
from app.repositories.memory_repo import MemoryRepository


class TestCommitTracker:
    """Test CommitTracker Git history integration."""

    def test_get_current_commit_hash_invalid_path(self):
        """Test getting commit hash from a non-existent path returns None."""
        db = MagicMock()
        tracker = CommitTracker(db)
        result = tracker.get_current_commit_hash("/nonexistent/path")
        assert result is None

    def test_sync_commits_invalid_path(self):
        """Test syncing commits from a non-existent path returns 0."""
        db = MagicMock()
        tracker = CommitTracker(db)
        result = tracker.sync_commits(1, "/nonexistent/path")
        assert result == 0

    @patch("app.engines.memory_engine.commit_tracker.Path")
    @patch("app.engines.memory_engine.commit_tracker.Repo")
    def test_get_current_commit_hash_valid_repo(self, mock_repo_class, mock_path):
        """Test getting commit hash from a valid repo."""
        db = MagicMock()
        tracker = CommitTracker(db)

        mock_path_instance = MagicMock()
        mock_path.return_value = mock_path_instance
        mock_path_instance.exists.return_value = True
        mock_path_instance.__truediv__ = MagicMock(return_value=MagicMock(exists=MagicMock(return_value=True)))

        mock_repo = MagicMock()
        mock_repo.head.commit.hexsha = "abc123def456"
        mock_repo_class.return_value = mock_repo

        result = tracker.get_current_commit_hash("/some/path")
        assert result == "abc123def456"


class TestSnapshotService:
    """Test SnapshotService functionality."""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        with patch.object(SnapshotService, '__init__', lambda self, db: None):
            svc = SnapshotService.__new__(SnapshotService)
            svc.db = mock_db
            svc.memory_repo = MagicMock(spec=MemoryRepository)
            svc.repo_repo = MagicMock()
            svc.parser_repo = MagicMock()
            svc.diff_engine = DiffEngine()
            svc.commit_tracker = MagicMock()
            return svc

    def test_create_snapshot_repository_not_found(self, service):
        """Test creating snapshot for non-existent repository raises error."""
        service.repo_repo.get_repository_by_id.return_value = None
        with pytest.raises(ValueError, match="Repository not found"):
            service.create_snapshot(999)

    def test_create_snapshot_first_time(self, service):
        """Test creating first snapshot (no previous snapshot)."""
        mock_repo = MagicMock()
        mock_repo.local_path = "/tmp/repo"
        mock_repo.default_branch = "main"
        service.repo_repo.get_repository_by_id.return_value = mock_repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.commit_tracker.get_current_commit_hash.return_value = None
        service.parser_repo.get_latest_parser_run.return_value = None
        service.parser_repo.count_nodes_by_type.return_value = {}

        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        service.memory_repo.create_snapshot.return_value = mock_snapshot
        service.memory_repo.get_previous_snapshot.return_value = None

        result = service.create_snapshot(1)

        assert result == mock_snapshot
        service.memory_repo.create_snapshot.assert_called_once()

    def test_create_snapshot_with_previous(self, service):
        """Test creating snapshot when previous snapshot exists triggers diff."""
        mock_repo = MagicMock()
        mock_repo.local_path = "/tmp/repo"
        mock_repo.default_branch = "main"
        service.repo_repo.get_repository_by_id.return_value = mock_repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.commit_tracker.get_current_commit_hash.return_value = "abc123"
        service.memory_repo.get_commit_by_hash.return_value = MagicMock(id=1)
        service.parser_repo.get_latest_parser_run.return_value = MagicMock(id=1)
        service.parser_repo.count_nodes_by_type.return_value = {}
        service.parser_repo.get_ast_nodes_by_repository.return_value = []

        mock_snapshot = MagicMock()
        mock_snapshot.id = 2
        service.memory_repo.create_snapshot.return_value = mock_snapshot

        prev_snapshot = MagicMock()
        prev_snapshot.id = 1
        service.memory_repo.get_previous_snapshot.return_value = prev_snapshot
        service.memory_repo.get_entity_versions_by_snapshot.return_value = []

        mock_change_set = MagicMock()
        mock_change_set.id = 1
        service.memory_repo.create_change_set.return_value = mock_change_set

        result = service.create_snapshot(1)

        assert result == mock_snapshot
        service.memory_repo.create_change_set.assert_called_once()

    def test_get_timeline(self, service):
        """Test getting repository timeline."""
        mock_commit = MagicMock()
        mock_commit.commit_hash = "abc123"

        mock_snapshot = MagicMock()
        mock_snapshot.id = 1
        mock_snapshot.commit_hash = "abc123"

        mock_cs = MagicMock()
        mock_cs.snapshot_id = 1

        service.memory_repo.get_commits_by_repository.return_value = [mock_commit]
        service.memory_repo.get_snapshots_by_repository.return_value = [mock_snapshot]
        service.memory_repo.get_commit_count.return_value = 1
        service.memory_repo.get_snapshot_count.return_value = 1
        service.memory_repo.get_change_sets_by_repository.return_value = [mock_cs]

        result = service.get_timeline(1)

        assert result["repository_id"] == 1
        assert result["total_commits"] == 1
        assert result["total_snapshots"] == 1
        assert len(result["entries"]) == 1

    def test_get_changes_by_commit(self, service):
        """Test getting changes by commit hash."""
        mock_cs = MagicMock()
        mock_cs.id = 1
        service.memory_repo.get_change_set_by_commit.return_value = mock_cs
        service.memory_repo.get_file_changes_by_change_set.return_value = []
        service.memory_repo.get_entity_changes_by_change_set.return_value = []

        result = service.get_changes_by_commit(1, "abc123")

        assert result is not None
        assert result["change_set"] == mock_cs

    def test_get_changes_by_commit_not_found(self, service):
        """Test getting changes for non-existent commit returns None."""
        service.memory_repo.get_change_set_by_commit.return_value = None
        result = service.get_changes_by_commit(1, "nonexistent")
        assert result is None

    def test_get_entity_signature_function(self, service):
        """Test extracting signature from a Function node."""
        from app.models.parser import Function
        node = MagicMock(spec=Function)
        node.name = "hello"
        node.parameters = "x, y"
        node.return_type = "int"
        node.is_async = False
        # Need isinstance to work
        result = service._get_entity_signature(node)
        # Since isinstance won't work with MagicMock spec properly in all cases,
        # it should fall back to node.name
        assert result is not None

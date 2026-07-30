"""Unit tests for GraphSyncService and GraphQueryService."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.engines.graph_engine.graph_sync_service import GraphSyncService
from app.engines.graph_engine.graph_query_service import GraphQueryService


class TestGraphSyncService:
    """Test GraphSyncService synchronization logic."""

    @pytest.fixture
    def mock_neo4j(self):
        client = MagicMock()
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"count": 1}
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        client.get_session.return_value = mock_session
        return client

    @pytest.fixture
    def service(self, mock_neo4j):
        with patch.object(GraphSyncService, '__init__', lambda self, db, neo4j: None):
            svc = GraphSyncService.__new__(GraphSyncService)
            svc.db = MagicMock()
            svc.neo4j = mock_neo4j
            svc.repo_repo = MagicMock()
            svc.parser_repo = MagicMock()
            svc.memory_repo = MagicMock()
            return svc

    def test_sync_repository_not_found(self, service):
        service.repo_repo.get_repository_by_id.return_value = None
        with pytest.raises(ValueError, match="Repository not found"):
            service.sync_repository(999)

    def test_sync_repository_returns_stats(self, service):
        repo = MagicMock()
        repo.name = "test"
        repo.url = "https://github.com/test/test"
        repo.local_path = "/tmp/test"
        repo.default_branch = "main"
        repo.description = "Test repo"
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = []
        service.memory_repo.get_snapshots_by_repository.return_value = []
        service.memory_repo.get_latest_snapshot.return_value = None
        service.memory_repo.get_change_sets_by_repository.return_value = []

        stats = service.sync_repository(1)

        assert "nodes_created" in stats
        assert "relationships_created" in stats
        assert "duration_seconds" in stats
        assert isinstance(stats["errors"], list)

    def test_sync_repository_creates_repo_node(self, service):
        repo = MagicMock()
        repo.name = "myrepo"
        repo.url = "https://github.com/u/myrepo"
        repo.local_path = "/tmp/myrepo"
        repo.default_branch = "main"
        repo.description = ""
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = []
        service.memory_repo.get_snapshots_by_repository.return_value = []
        service.memory_repo.get_latest_snapshot.return_value = None
        service.memory_repo.get_change_sets_by_repository.return_value = []

        stats = service.sync_repository(1)
        assert stats["nodes_created"] >= 1  # At least the repo node

    def test_sync_commits(self, service):
        commit = MagicMock()
        commit.commit_hash = "abc123"
        commit.author_name = "Test"
        commit.author_email = "test@test.com"
        commit.message = "Initial commit"
        commit.branch = "main"
        commit.committed_at = None

        repo = MagicMock()
        repo.name = "r"
        repo.url = "u"
        repo.local_path = "/tmp"
        repo.default_branch = "main"
        repo.description = ""
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = [commit]
        service.memory_repo.get_snapshots_by_repository.return_value = []
        service.memory_repo.get_latest_snapshot.return_value = None
        service.memory_repo.get_change_sets_by_repository.return_value = []

        stats = service.sync_repository(1)
        assert stats["nodes_created"] >= 2  # repo + commit

    def test_sync_files_creates_file_and_dir_nodes(self, service):
        repo = MagicMock()
        repo.name = "r"
        repo.url = "u"
        repo.local_path = "/tmp"
        repo.default_branch = "main"
        repo.description = ""
        service.repo_repo.get_repository_by_id.return_value = repo

        file1 = MagicMock()
        file1.id = 1
        file1.file_name = "main.py"
        file1.relative_path = "src/main.py"
        file1.extension = ".py"
        file1.language = "Python"
        file1.size_bytes = 100
        file1.sha256_checksum = "abc"
        service.repo_repo.get_files_by_repository.return_value = [file1]

        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = []
        service.memory_repo.get_snapshots_by_repository.return_value = []
        service.memory_repo.get_latest_snapshot.return_value = None
        service.memory_repo.get_change_sets_by_repository.return_value = []

        stats = service.sync_repository(1)
        # Repo node + directory node (src) + file node
        assert stats["nodes_created"] >= 3

    def test_sync_dependencies(self, service):
        repo = MagicMock()
        repo.name = "r"
        repo.url = "u"
        repo.local_path = "/tmp"
        repo.default_branch = "main"
        repo.description = ""
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []

        dep = MagicMock()
        dep.name = "requests"
        dep.version = "2.31.0"
        dep.package_manager = "pip"
        dep.source_file = None
        service.repo_repo.get_dependencies_by_repository.return_value = [dep]
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = []
        service.memory_repo.get_snapshots_by_repository.return_value = []
        service.memory_repo.get_latest_snapshot.return_value = None
        service.memory_repo.get_change_sets_by_repository.return_value = []

        stats = service.sync_repository(1)
        assert stats["nodes_created"] >= 2  # repo + dependency

    def test_sync_handles_errors_gracefully(self, service):
        repo = MagicMock()
        repo.name = "r"
        repo.url = "u"
        repo.local_path = "/tmp"
        repo.default_branch = "main"
        repo.description = ""
        service.repo_repo.get_repository_by_id.return_value = repo

        # Make commits fail
        service.memory_repo.get_commits_by_repository.side_effect = Exception("DB error")
        service.repo_repo.get_files_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_snapshots_by_repository.return_value = []
        service.memory_repo.get_latest_snapshot.return_value = None
        service.memory_repo.get_change_sets_by_repository.return_value = []

        # Should not raise — errors are recorded
        stats = service.sync_repository(1)
        assert isinstance(stats["errors"], list)

    def test_handle_deletions(self, service):
        """Test that deleted files/entities are processed."""
        repo = MagicMock()
        repo.name = "r"
        repo.url = "u"
        repo.local_path = "/tmp"
        repo.default_branch = "main"
        repo.description = ""
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = []
        service.memory_repo.get_snapshots_by_repository.return_value = []

        snapshot = MagicMock()
        snapshot.id = 5
        service.memory_repo.get_latest_snapshot.return_value = snapshot

        cs = MagicMock()
        cs.id = 10
        cs.snapshot_id = 5
        service.memory_repo.get_change_sets_by_repository.return_value = [cs]

        fc = MagicMock()
        fc.change_type = "deleted"
        fc.file_path = "old/removed.py"
        service.memory_repo.get_file_changes_by_change_set.return_value = [fc]

        ec = MagicMock()
        ec.change_type = "deleted"
        ec.entity_name = "OldClass"
        ec.file_path = "old/removed.py"
        service.memory_repo.get_entity_changes_by_change_set.return_value = [ec]

        stats = service.sync_repository(1)
        assert stats["nodes_deleted"] >= 2  # file + entity


class TestGraphQueryService:
    """Test GraphQueryService read-only queries."""

    @pytest.fixture
    def mock_neo4j(self):
        client = MagicMock()
        mock_session = MagicMock()
        mock_session.__enter__ = MagicMock(return_value=mock_session)
        mock_session.__exit__ = MagicMock(return_value=False)
        client.get_session.return_value = mock_session
        return client

    @pytest.fixture
    def query_service(self, mock_neo4j):
        return GraphQueryService(mock_neo4j)

    def test_get_statistics(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        # First call: label counts
        mock_records = [
            MagicMock(items=lambda: [("label", "File"), ("count", 10)]),
        ]
        mock_records[0].__getitem__ = lambda self, key: {"label": "File", "count": 10}[key]
        session.run.return_value = iter(mock_records)

        result = query_service.get_statistics(1)
        assert result["repository_id"] == 1

    def test_get_node_not_found(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value.single.return_value = None
        result = query_service.get_node("nonexistent")
        assert result is None

    def test_get_node_found(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        mock_node = {"uid": "file:1", "name": "main.py"}
        mock_record = MagicMock()
        mock_record.__getitem__ = lambda s, k: {"n": mock_node, "labels": ["File"]}[k]
        session.run.return_value.single.return_value = mock_record

        result = query_service.get_node("4:abc:1")
        assert result is not None
        assert result["element_id"] == "4:abc:1"
        assert result["labels"] == ["File"]

    def test_get_neighbors_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.get_neighbors("4:abc:1")
        assert result == []

    def test_most_connected_files_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.most_connected_files(1)
        assert result == []

    def test_largest_classes_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.largest_classes(1)
        assert result == []

    def test_dependency_graph_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.dependency_graph(1)
        assert result == []

    def test_import_graph_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.import_graph(1)
        assert result == []

    def test_call_graph_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.call_graph(1)
        assert result == []

    def test_language_statistics_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.language_statistics(1)
        assert result == []

    def test_framework_statistics_empty(self, query_service, mock_neo4j):
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.return_value = iter([])
        result = query_service.framework_statistics(1)
        assert result == []

    def test_query_service_handles_neo4j_errors(self, query_service, mock_neo4j):
        """Service should not crash when Neo4j is unavailable."""
        session = mock_neo4j.get_session.return_value.__enter__.return_value
        session.run.side_effect = Exception("Connection refused")

        # All methods should return empty results, not raise
        assert query_service.most_connected_files(1) == []
        assert query_service.largest_classes(1) == []
        assert query_service.dependency_graph(1) == []
        assert query_service.import_graph(1) == []
        assert query_service.call_graph(1) == []
        assert query_service.language_statistics(1) == []
        assert query_service.framework_statistics(1) == []

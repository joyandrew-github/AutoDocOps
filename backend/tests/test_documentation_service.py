"""Unit tests for DocumentationService."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from app.engines.documentation_engine.documentation_service import DocumentationService


class TestDocumentationService:
    """Test DocumentationService orchestration logic."""

    @pytest.fixture
    def service(self):
        with patch.object(DocumentationService, '__init__', lambda self, db: None):
            svc = DocumentationService.__new__(DocumentationService)
            svc.db = MagicMock()
            svc.generator = MagicMock()
            svc.doc_repo = MagicMock()
            svc.repo_repo = MagicMock()
            svc.parser_repo = MagicMock()
            svc.memory_repo = MagicMock()
            return svc

    # --- generate_documentation ---

    def test_generate_repo_not_found(self, service):
        service.repo_repo.get_repository_by_id.return_value = None
        with pytest.raises(ValueError, match="Repository not found"):
            service.generate_documentation(999)

    def test_generate_returns_stats(self, service):
        repo = MagicMock()
        repo.name = "TestRepo"
        repo.description = "Test"
        service.repo_repo.get_repository_by_id.return_value = repo
        service.memory_repo.get_change_sets_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_files_by_repository.return_value = []
        service.parser_repo.count_nodes_by_type.return_value = {}
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.parser_repo.get_classes_by_repository.return_value = []
        service.parser_repo.get_functions_by_repository.return_value = []
        service.memory_repo.get_commits_by_repository.return_value = []

        job = MagicMock()
        service.doc_repo.create_job.return_value = job

        service.generator.generate_repository_overview.return_value = ("content", "summary", [])
        service.generator.generate_changelog.return_value = ("content", "summary", [])
        service.generator.generate_onboarding_guide.return_value = ("content", "summary", [])
        service.doc_repo.get_documentation_by_slug.return_value = None

        doc = MagicMock()
        doc.id = 1
        service.doc_repo.create_documentation.return_value = doc

        stats = service.generate_documentation(1)
        assert "documents_created" in stats
        assert "documents_updated" in stats
        assert "documents_skipped" in stats
        assert isinstance(stats["errors"], list)

    def test_generate_specific_doc_types(self, service):
        repo = MagicMock()
        repo.name = "Repo"
        repo.description = None
        service.repo_repo.get_repository_by_id.return_value = repo
        service.memory_repo.get_change_sets_by_repository.return_value = []
        service.repo_repo.get_languages_by_repository.return_value = []
        service.repo_repo.get_frameworks_by_repository.return_value = []
        service.repo_repo.get_dependencies_by_repository.return_value = []
        service.repo_repo.get_files_by_repository.return_value = []

        job = MagicMock()
        service.doc_repo.create_job.return_value = job

        service.generator.generate_repository_overview.return_value = ("c", "s", [])
        service.doc_repo.get_documentation_by_slug.return_value = None
        doc = MagicMock()
        doc.id = 1
        service.doc_repo.create_documentation.return_value = doc
        service.parser_repo.count_nodes_by_type.return_value = {}

        stats = service.generate_documentation(1, doc_types=["repository_overview"])
        assert isinstance(stats, dict)
        # Should not have called changelog generator
        service.generator.generate_changelog.assert_not_called()

    def test_generate_handles_job_failure(self, service):
        repo = MagicMock()
        repo.name = "Repo"
        service.repo_repo.get_repository_by_id.return_value = repo
        job = MagicMock()
        service.doc_repo.create_job.return_value = job
        service.memory_repo.get_change_sets_by_repository.side_effect = Exception("DB error")

        stats = service.generate_documentation(1)
        assert len(stats["errors"]) > 0
        service.doc_repo.update_job.assert_called()

    # --- handle_deletions ---

    def test_handle_deletions_deletes_files(self, service):
        stats = {"errors": []}
        snapshot = MagicMock()
        snapshot.id = 5
        service.memory_repo.get_latest_snapshot.return_value = snapshot

        cs = MagicMock()
        cs.id = 10
        cs.snapshot_id = 5
        service.memory_repo.get_change_sets_by_repository.return_value = [cs]

        fc = MagicMock()
        fc.change_type = "deleted"
        fc.file_path = "removed.py"
        service.memory_repo.get_file_changes_by_change_set.return_value = [fc]

        ec = MagicMock()
        ec.change_type = "deleted"
        ec.entity_type = "function"
        ec.entity_name = "old_fn"
        ec.file_path = "removed.py"
        service.memory_repo.get_entity_changes_by_change_set.return_value = [ec]

        service._handle_deletions(1, stats)
        service.doc_repo.delete_documentation_by_file.assert_called_once()
        service.doc_repo.delete_documentation_by_entity.assert_called_once()

    def test_handle_deletions_no_changes(self, service):
        stats = {"errors": []}
        service.memory_repo.get_change_sets_by_repository.return_value = []
        service._handle_deletions(1, stats)
        assert stats["errors"] == []

    # --- _store_or_update ---

    def test_store_new_document(self, service):
        stats = {"documents_created": 0, "documents_updated": 0, "documents_skipped": 0}
        service.doc_repo.get_documentation_by_slug.return_value = None
        doc = MagicMock()
        doc.id = 1
        service.doc_repo.create_documentation.return_value = doc

        service._store_or_update(1, "file", "Title", "slug", "content", "summary", [], stats)
        assert stats["documents_created"] == 1

    def test_store_skip_unchanged(self, service):
        import hashlib
        content = "same content"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing = MagicMock()
        existing.content_hash = content_hash
        service.doc_repo.get_documentation_by_slug.return_value = existing

        stats = {"documents_created": 0, "documents_updated": 0, "documents_skipped": 0}
        service._store_or_update(1, "file", "Title", "slug", content, "summary", [], stats)
        assert stats["documents_skipped"] == 1

    def test_store_update_changed(self, service):
        existing = MagicMock()
        existing.id = 1
        existing.version = 1
        existing.content = "old"
        existing.content_hash = "oldhash"
        service.doc_repo.get_documentation_by_slug.return_value = existing

        stats = {"documents_created": 0, "documents_updated": 0, "documents_skipped": 0}
        service._store_or_update(1, "file", "Title", "slug", "new content", "summary", [], stats)
        assert stats["documents_updated"] == 1
        service.doc_repo.create_version.assert_called_once()

    # --- slugify ---

    def test_slugify(self, service):
        assert service._slugify("Hello World!") == "hello-world"
        assert service._slugify("  spaces  ") == "spaces"
        assert service._slugify("a/b/c") == "abc"

    # --- get/search/export ---

    def test_get_documentation(self, service):
        service.doc_repo.get_documentations_by_repository.return_value = []
        assert service.get_documentation(1) == []

    def test_get_documentation_by_id(self, service):
        service.doc_repo.get_documentation_by_id.return_value = None
        assert service.get_documentation_by_id(1) is None

    def test_search_documentation(self, service):
        service.doc_repo.search_documentations.return_value = []
        assert service.search_documentation(1, "query") == []

    def test_export_markdown(self, service):
        doc = MagicMock()
        doc.content = "# Hello"
        doc.title = "Hello"
        service.doc_repo.get_documentation_by_id.return_value = doc
        result = service.export_documentation(1, "markdown")
        assert result == "# Hello"

    def test_export_html(self, service):
        doc = MagicMock()
        doc.content = "# Hello"
        doc.title = "Hello"
        service.doc_repo.get_documentation_by_id.return_value = doc
        service.generator.to_html.return_value = "<h1>Hello</h1>"
        result = service.export_documentation(1, "html")
        assert "<h1>" in result

    def test_export_pdf(self, service):
        doc = MagicMock()
        doc.content = "# Hello"
        doc.title = "Hello"
        service.doc_repo.get_documentation_by_id.return_value = doc
        service.generator.to_pdf_ready_markdown.return_value = "---\ntitle: Hello\n---\n# Hello"
        result = service.export_documentation(1, "pdf")
        assert "title:" in result

    def test_export_not_found(self, service):
        service.doc_repo.get_documentation_by_id.return_value = None
        assert service.export_documentation(999) is None

    def test_export_all(self, service):
        doc = MagicMock()
        doc.id = 1
        doc.title = "Doc"
        doc.doc_type = "file"
        doc.content = "# Content"
        service.doc_repo.get_documentations_by_repository.return_value = [doc]
        results = service.export_all(1, "markdown")
        assert len(results) == 1
        assert results[0]["content"] == "# Content"

    def test_export_all_html(self, service):
        doc = MagicMock()
        doc.id = 1
        doc.title = "Doc"
        doc.doc_type = "file"
        doc.content = "# Content"
        service.doc_repo.get_documentations_by_repository.return_value = [doc]
        service.generator.to_html.return_value = "<h1>Content</h1>"
        results = service.export_all(1, "html")
        assert "<h1>" in results[0]["content"]

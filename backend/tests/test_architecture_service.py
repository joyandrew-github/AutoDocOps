"""Unit tests for ArchitectureService."""
import pytest
from unittest.mock import MagicMock, patch
from app.engines.architecture_engine.architecture_service import ArchitectureService


class TestArchitectureService:

    @pytest.fixture
    def service(self):
        with patch.object(ArchitectureService, '__init__', lambda self, db: None):
            svc = ArchitectureService.__new__(ArchitectureService)
            svc.db = MagicMock()
            svc.analyzer = MagicMock()
            svc.diagram_gen = MagicMock()
            svc.arch_repo = MagicMock()
            svc.repo_repo = MagicMock()
            svc.parser_repo = MagicMock()
            svc.memory_repo = MagicMock()
            return svc

    # --- generate_architecture ---

    def test_generate_repo_not_found(self, service):
        service.repo_repo.get_repository_by_id.return_value = None
        with pytest.raises(ValueError, match="Repository not found"):
            service.generate_architecture(999)

    def test_generate_returns_stats(self, service):
        repo = MagicMock()
        repo.name = "TestRepo"
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []

        snapshot = MagicMock()
        service.arch_repo.create_snapshot.return_value = snapshot

        service.analyzer.analyze_layers.return_value = {"layers": {}}
        service.analyzer.analyze_modules.return_value = {"modules": {}}
        service.analyzer.analyze_components.return_value = {"components": {}}
        service.analyzer.analyze_dependencies.return_value = {"file_dependencies": {}, "module_dependencies": {}}
        service.analyzer.analyze_call_graph.return_value = {"nodes": [], "edges": []}
        service.analyzer.identify_entry_points.return_value = []
        service.analyzer.identify_apis.return_value = []
        service.analyzer.detect_circular_dependencies.return_value = []
        service.analyzer.detect_layer_violations.return_value = []

        service.arch_repo.get_model_by_type.return_value = None
        model = MagicMock()
        model.id = 1
        service.arch_repo.create_model.return_value = model

        stats = service.generate_architecture(1)
        assert "models_created" in stats
        assert "diagrams_generated" in stats
        assert "violations_detected" in stats
        assert isinstance(stats["errors"], list)

    def test_generate_handles_failure(self, service):
        repo = MagicMock()
        service.repo_repo.get_repository_by_id.return_value = repo
        snapshot = MagicMock()
        service.arch_repo.create_snapshot.return_value = snapshot
        service.repo_repo.get_files_by_repository.side_effect = Exception("DB error")

        stats = service.generate_architecture(1)
        assert len(stats["errors"]) > 0
        service.arch_repo.update_snapshot.assert_called()

    def test_generate_with_violations(self, service):
        repo = MagicMock()
        service.repo_repo.get_repository_by_id.return_value = repo
        service.repo_repo.get_files_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        snapshot = MagicMock()
        service.arch_repo.create_snapshot.return_value = snapshot

        service.analyzer.analyze_layers.return_value = {"layers": {}}
        service.analyzer.analyze_modules.return_value = {"modules": {}}
        service.analyzer.analyze_components.return_value = {"components": {}}
        service.analyzer.analyze_dependencies.return_value = {"file_dependencies": {}, "module_dependencies": {}}
        service.analyzer.analyze_call_graph.return_value = {"nodes": [], "edges": []}
        service.analyzer.identify_entry_points.return_value = []
        service.analyzer.identify_apis.return_value = []
        service.analyzer.detect_circular_dependencies.return_value = [
            {"cycle": ["a", "b", "a"], "description": "Circular dependency: a → b → a"}
        ]
        service.analyzer.detect_layer_violations.return_value = [
            {"violation_type": "layer_violation", "severity": "warning", "description": "Bad import", "source_entity": "a", "target_entity": "b", "source_file": "a.py", "source_layer": "repo", "target_layer": "api"}
        ]

        service.arch_repo.get_model_by_type.return_value = None
        model = MagicMock()
        model.id = 1
        service.arch_repo.create_model.return_value = model

        stats = service.generate_architecture(1)
        assert stats["violations_detected"] == 2

    # --- _store_model ---

    def test_store_new_model(self, service):
        stats = {"models_created": 0, "models_updated": 0, "models_skipped": 0}
        service.arch_repo.get_model_by_type.return_value = None
        model = MagicMock()
        model.id = 1
        service.arch_repo.create_model.return_value = model
        service._store_model(1, "layers", "Layers", "desc", {"test": True}, stats)
        assert stats["models_created"] == 1

    def test_store_skip_unchanged(self, service):
        import hashlib, json
        data = {"test": True}
        content_hash = hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
        existing = MagicMock()
        existing.content_hash = content_hash
        service.arch_repo.get_model_by_type.return_value = existing
        stats = {"models_created": 0, "models_updated": 0, "models_skipped": 0}
        service._store_model(1, "layers", "Layers", "desc", data, stats)
        assert stats["models_skipped"] == 1

    def test_store_update_changed(self, service):
        existing = MagicMock()
        existing.content_hash = "oldhash"
        existing.version = 1
        service.arch_repo.get_model_by_type.return_value = existing
        stats = {"models_created": 0, "models_updated": 0, "models_skipped": 0}
        service._store_model(1, "layers", "Layers", "desc", {"new": True}, stats)
        assert stats["models_updated"] == 1

    # --- getter methods ---

    def test_get_architecture(self, service):
        service.arch_repo.get_models_by_repository.return_value = []
        assert service.get_architecture(1) == []

    def test_get_architecture_by_id(self, service):
        service.arch_repo.get_model_by_id.return_value = None
        assert service.get_architecture_by_id(1) is None

    def test_get_dependencies(self, service):
        model = MagicMock()
        model.data = {"file_dependencies": {}}
        service.arch_repo.get_model_by_type.return_value = model
        result = service.get_dependencies(1)
        assert result == {"file_dependencies": {}}

    def test_get_dependencies_none(self, service):
        service.arch_repo.get_model_by_type.return_value = None
        assert service.get_dependencies(1) is None

    def test_get_callgraph(self, service):
        model = MagicMock()
        model.data = {"nodes": []}
        service.arch_repo.get_model_by_type.return_value = model
        assert service.get_callgraph(1) == {"nodes": []}

    def test_get_callgraph_none(self, service):
        service.arch_repo.get_model_by_type.return_value = None
        assert service.get_callgraph(1) is None

    def test_get_violations(self, service):
        service.arch_repo.get_violations_by_repository.return_value = []
        assert service.get_violations(1) == []

    def test_get_diagrams(self, service):
        service.arch_repo.get_diagrams_by_repository.return_value = []
        assert service.get_diagrams(1) == []

    def test_get_diagrams_filtered(self, service):
        d = MagicMock()
        d.format = "mermaid"
        service.arch_repo.get_diagrams_by_repository.return_value = [d]
        assert service.get_diagrams(1, format="mermaid") == [d]
        assert service.get_diagrams(1, format="plantuml") == []

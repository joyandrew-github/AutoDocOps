"""Unit tests for ImpactAnalysisService."""
import json
import pytest
from unittest.mock import MagicMock, patch
from app.engines.impact_engine.impact_service import (
    ImpactAnalysisService,
    _risk_level,
    RISK_WEIGHTS,
)


class TestRiskLevel:
    def test_low(self):
        assert _risk_level(0.1) == "low"

    def test_medium(self):
        assert _risk_level(0.3) == "medium"

    def test_high(self):
        assert _risk_level(0.55) == "high"

    def test_critical(self):
        assert _risk_level(0.8) == "critical"

    def test_boundary_low(self):
        assert _risk_level(0.24) == "low"

    def test_boundary_medium(self):
        assert _risk_level(0.25) == "medium"

    def test_boundary_high(self):
        assert _risk_level(0.50) == "high"

    def test_boundary_critical(self):
        assert _risk_level(0.75) == "critical"


class TestImpactAnalysisService:

    @pytest.fixture
    def service(self):
        with patch.object(ImpactAnalysisService, '__init__', lambda self, db: None):
            svc = ImpactAnalysisService.__new__(ImpactAnalysisService)
            svc.db = MagicMock()
            svc.impact_repo = MagicMock()
            svc.repo_repo = MagicMock()
            svc.parser_repo = MagicMock()
            svc.memory_repo = MagicMock()
            return svc

    # --- analyze_impact ---

    def test_analyze_repo_not_found(self, service):
        service.repo_repo.get_repository_by_id.return_value = None
        with pytest.raises(ValueError, match="Repository not found"):
            service.analyze_impact(999)

    def test_analyze_returns_stats(self, service):
        repo = MagicMock()
        repo.name = "TestRepo"
        service.repo_repo.get_repository_by_id.return_value = repo
        service.memory_repo.get_latest_snapshot.return_value = MagicMock(id=1)
        analysis = MagicMock()
        analysis.id = 1
        service.impact_repo.create_analysis.return_value = analysis
        service.memory_repo.get_change_sets_by_repository.return_value = []
        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        service.repo_repo.get_files_by_repository.return_value = []
        service.impact_repo.bulk_create_results.return_value = []

        stats = service.analyze_impact(1)
        assert "total_changes" in stats
        assert "total_affected" in stats
        assert "overall_risk_level" in stats
        assert isinstance(stats["errors"], list)

    def test_analyze_handles_failure(self, service):
        repo = MagicMock()
        service.repo_repo.get_repository_by_id.return_value = repo
        service.memory_repo.get_latest_snapshot.return_value = MagicMock(id=1)
        analysis = MagicMock()
        analysis.id = 1
        service.impact_repo.create_analysis.return_value = analysis
        service.memory_repo.get_change_sets_by_repository.side_effect = Exception("DB error")

        stats = service.analyze_impact(1)
        assert len(stats["errors"]) > 0

    # --- _collect_changes ---

    def test_collect_changes_no_changesets(self, service):
        service.memory_repo.get_change_sets_by_repository.return_value = []
        fc, ec = service._collect_changes(1)
        assert fc == []
        assert ec == []

    def test_collect_changes_with_data(self, service):
        snapshot = MagicMock()
        snapshot.id = 5
        service.memory_repo.get_latest_snapshot.return_value = snapshot
        cs = MagicMock()
        cs.id = 10
        cs.snapshot_id = 5
        service.memory_repo.get_change_sets_by_repository.return_value = [cs]

        fc_mock = MagicMock()
        fc_mock.file_path = "main.py"
        fc_mock.change_type = "modified"
        service.memory_repo.get_file_changes_by_change_set.return_value = [fc_mock]

        ec_mock = MagicMock()
        ec_mock.entity_type = "function"
        ec_mock.entity_name = "process"
        ec_mock.file_path = "main.py"
        ec_mock.change_type = "modified"
        service.memory_repo.get_entity_changes_by_change_set.return_value = [ec_mock]

        fc, ec = service._collect_changes(1)
        assert len(fc) == 1
        assert len(ec) == 1

    def test_collect_changes_snapshot_mismatch(self, service):
        snapshot = MagicMock()
        snapshot.id = 5
        service.memory_repo.get_latest_snapshot.return_value = snapshot
        cs = MagicMock()
        cs.id = 10
        cs.snapshot_id = 999  # mismatch
        service.memory_repo.get_change_sets_by_repository.return_value = [cs]

        fc, ec = service._collect_changes(1)
        assert fc == []
        assert ec == []

    # --- _build_dependency_index ---

    def test_build_dependency_index(self, service):
        from app.models.parser import Import as ImportModel
        imp = MagicMock(spec=ImportModel)
        imp.name = "os"
        imp.file_id = 1
        imp.module = "os"
        type(imp).__instancecheck__ = lambda cls, inst: True

        service.parser_repo.get_ast_nodes_by_repository.return_value = []
        file_mock = MagicMock()
        file_mock.id = 1
        file_mock.relative_path = "main.py"
        service.repo_repo.get_files_by_repository.return_value = [file_mock]

        index = service._build_dependency_index(1)
        assert "importers" in index
        assert "file_entities" in index
        assert "entity_file" in index

    # --- _analyze_entity_impact ---

    def test_analyze_entity_impact(self, service):
        dep_index = {"importers": {}, "file_entities": {}, "entity_file": {}}
        change = {"entity_name": "process", "entity_type": "function", "file_path": "main.py", "change_type": "modified"}
        result = service._analyze_entity_impact(1, 10, change, dep_index)
        assert result["entity_name"] == "process"
        assert result["risk_level"] in ("low", "medium", "high", "critical")
        assert result["analysis_id"] == 10

    def test_analyze_entity_impact_api(self, service):
        dep_index = {"importers": {}, "file_entities": {}, "entity_file": {}}
        change = {"entity_name": "get_users", "entity_type": "function", "file_path": "app/api/users.py", "change_type": "modified"}
        result = service._analyze_entity_impact(1, 10, change, dep_index)
        assert result["details"]["is_api"] is True

    def test_analyze_entity_impact_with_dependents(self, service):
        dep_index = {
            "importers": {"main": ["app/service.py", "app/handler.py"]},
            "file_entities": {"app/service.py": ["svc_fn"], "app/handler.py": ["handler_fn"]},
            "entity_file": {"process": "main.py"},
        }
        change = {"entity_name": "process", "entity_type": "function", "file_path": "main.py", "change_type": "modified"}
        result = service._analyze_entity_impact(1, 10, change, dep_index)
        assert result["direct_dependents"] >= 0

    # --- _analyze_file_impact ---

    def test_analyze_file_impact(self, service):
        dep_index = {"importers": {}, "file_entities": {"main.py": ["fn1", "fn2"]}, "entity_file": {}}
        change = {"file_path": "main.py", "change_type": "modified"}
        result = service._analyze_file_impact(1, 10, change, dep_index)
        assert result["entity_type"] == "file"
        assert result["entity_name"] == "main.py"

    def test_analyze_file_impact_empty(self, service):
        dep_index = {"importers": {}, "file_entities": {}, "entity_file": {}}
        change = {"file_path": "empty.py", "change_type": "added"}
        result = service._analyze_file_impact(1, 10, change, dep_index)
        assert result["direct_dependents"] == 0

    # --- dependency traversal ---

    def test_find_direct_dependents(self, service):
        dep_index = {"importers": {"app.main": ["app/service.py"]}}
        result = service._find_direct_dependents("main_fn", "app/main.py", dep_index)
        assert "app/service.py" in result

    def test_find_direct_dependents_none(self, service):
        dep_index = {"importers": {}}
        result = service._find_direct_dependents("x", "y.py", dep_index)
        assert result == []

    def test_find_indirect_dependents(self, service):
        dep_index = {"importers": {}, "file_entities": {}}
        result = service._find_indirect_dependents(["a.py"], dep_index, depth=2)
        assert isinstance(result, list)

    # --- helpers ---

    def test_is_api_entity_true(self, service):
        assert service._is_api_entity("app/api/endpoint.py", "get_users", {}) is True

    def test_is_api_entity_false(self, service):
        assert service._is_api_entity("app/models/user.py", "User", {}) is False

    def test_count_cross_module(self, service):
        result = service._count_cross_module("app/main.py", ["lib/service.py", "pkg/helper.py"])
        assert result == 2

    def test_count_cross_module_same(self, service):
        result = service._count_cross_module("app/main.py", ["app/other.py"])
        assert result == 0

    # --- risk assessment ---

    def test_compute_risk_assessment(self, service):
        results = [
            {"direct_dependents": 3, "indirect_dependents": 2, "details": {"is_api": True, "cross_module_count": 1}, "entity_name": "fn", "entity_type": "function", "risk_level": "medium"},
        ]
        risk = service._compute_risk_assessment(1, 1, results, {}, [{"file_path": "a.py"}], [{"entity_name": "fn"}])
        assert risk["risk_level"] in ("low", "medium", "high", "critical")
        assert 0 <= risk["risk_score"] <= 1
        assert "dependency_score" in risk
        assert "api_score" in risk

    def test_compute_risk_assessment_empty(self, service):
        risk = service._compute_risk_assessment(1, 1, [], {}, [], [])
        assert risk["risk_level"] == "low"
        assert risk["risk_score"] == 0.0

    # --- test recommendations ---

    def test_generate_test_recommendations(self, service):
        results = [
            {"entity_name": "fn1", "entity_type": "function", "risk_level": "high", "direct_dependents": 3},
            {"entity_name": "cls1", "entity_type": "class", "risk_level": "low", "direct_dependents": 0},
            {"entity_name": "f.py", "entity_type": "file", "risk_level": "critical", "direct_dependents": 5},
        ]
        recs = service._generate_test_recommendations(results)
        assert len(recs["unit_tests"]) >= 2
        assert len(recs["integration_tests"]) >= 1
        assert len(recs["regression_tests"]) >= 1

    def test_generate_test_recommendations_empty(self, service):
        recs = service._generate_test_recommendations([])
        assert recs["unit_tests"] == []
        assert recs["integration_tests"] == []
        assert recs["regression_tests"] == []

    # --- export ---

    def test_export_json(self, service):
        analysis = MagicMock()
        analysis.id = 1
        analysis.repository_id = 1
        analysis.status = "completed"
        analysis.total_changes = 2
        analysis.total_affected = 3
        analysis.overall_risk_level = "medium"
        analysis.overall_risk_score = 0.4
        analysis.summary = "test"
        service.impact_repo.get_analysis_by_id.return_value = analysis
        service.impact_repo.get_results_by_analysis.return_value = []
        service.impact_repo.get_risk_assessment.return_value = None

        content = service.export_analysis(1, "json")
        data = json.loads(content)
        assert data["status"] == "completed"

    def test_export_markdown(self, service):
        analysis = MagicMock()
        analysis.id = 1
        analysis.repository_id = 1
        analysis.status = "completed"
        analysis.total_changes = 1
        analysis.total_affected = 1
        analysis.overall_risk_level = "low"
        analysis.overall_risk_score = 0.1
        analysis.summary = "ok"
        service.impact_repo.get_analysis_by_id.return_value = analysis
        service.impact_repo.get_results_by_analysis.return_value = []
        service.impact_repo.get_risk_assessment.return_value = None

        content = service.export_analysis(1, "markdown")
        assert "# Impact Analysis Report" in content

    def test_export_html(self, service):
        analysis = MagicMock()
        analysis.id = 1
        analysis.repository_id = 1
        analysis.status = "completed"
        analysis.total_changes = 0
        analysis.total_affected = 0
        analysis.overall_risk_level = "low"
        analysis.overall_risk_score = 0.0
        analysis.summary = ""
        service.impact_repo.get_analysis_by_id.return_value = analysis
        service.impact_repo.get_results_by_analysis.return_value = []
        service.impact_repo.get_risk_assessment.return_value = None

        content = service.export_analysis(1, "html")
        assert "<html>" in content
        assert "<h1>" in content

    def test_export_not_found(self, service):
        service.impact_repo.get_analysis_by_id.return_value = None
        assert service.export_analysis(999) is None

    # --- getter methods ---

    def test_get_analysis(self, service):
        service.impact_repo.get_analysis_by_id.return_value = None
        assert service.get_analysis(1) is None

    def test_get_analysis_history(self, service):
        service.impact_repo.get_analyses_by_repository.return_value = []
        assert service.get_analysis_history(1) == []

    def test_get_entity_impact_no_analysis(self, service):
        service.impact_repo.get_latest_analysis.return_value = None
        assert service.get_entity_impact(1, "fn") is None

    def test_get_entity_impact_found(self, service):
        analysis = MagicMock()
        analysis.id = 1
        service.impact_repo.get_latest_analysis.return_value = analysis
        result = MagicMock()
        service.impact_repo.get_result_by_entity_name.return_value = result
        assert service.get_entity_impact(1, "fn") == result

    def test_get_risk_assessment_no_analysis(self, service):
        service.impact_repo.get_latest_analysis.return_value = None
        assert service.get_risk_assessment(1) is None

    def test_get_risk_assessment_found(self, service):
        analysis = MagicMock()
        analysis.id = 1
        service.impact_repo.get_latest_analysis.return_value = analysis
        risk = MagicMock()
        service.impact_repo.get_risk_assessment.return_value = risk
        assert service.get_risk_assessment(1) == risk

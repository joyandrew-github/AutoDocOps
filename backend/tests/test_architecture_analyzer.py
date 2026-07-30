"""Unit tests for ArchitectureAnalyzer."""
import pytest
from app.engines.architecture_engine.analyzer import ArchitectureAnalyzer


class TestArchitectureAnalyzer:

    @pytest.fixture
    def analyzer(self):
        return ArchitectureAnalyzer()

    # --- analyze_layers ---

    def test_analyze_layers_assigns_correctly(self, analyzer):
        files = [
            {"relative_path": "app/api/v1/endpoints/health.py"},
            {"relative_path": "app/services/repo_service.py"},
            {"relative_path": "app/models/user.py"},
            {"relative_path": "app/repositories/user_repo.py"},
            {"relative_path": "app/utils/helpers.py"},
            {"relative_path": "app/config/settings.py"},
            {"relative_path": "tests/test_user.py"},
        ]
        result = analyzer.analyze_layers(files)
        assert "api" in result["layers"]
        assert "service" in result["layers"]
        assert "model" in result["layers"]
        assert "repository" in result["layers"]
        assert "util" in result["layers"]
        assert "config" in result["layers"]
        assert "test" in result["layers"]
        assert result["file_count"] == 7

    def test_analyze_layers_unassigned(self, analyzer):
        files = [{"relative_path": "random_file.txt"}]
        result = analyzer.analyze_layers(files)
        assert result["unassigned"] == ["random_file.txt"]

    def test_analyze_layers_empty(self, analyzer):
        result = analyzer.analyze_layers([])
        assert result["layer_count"] == 0

    # --- analyze_modules ---

    def test_analyze_modules(self, analyzer):
        files = [
            {"relative_path": "src/utils/helper.py", "language": "Python"},
            {"relative_path": "src/utils/math.py", "language": "Python"},
            {"relative_path": "src/main.py", "language": "Python"},
        ]
        result = analyzer.analyze_modules(files)
        assert "src/utils" in result["modules"]
        assert result["modules"]["src/utils"]["file_count"] == 2
        assert "Python" in result["modules"]["src/utils"]["languages"]
        assert result["module_count"] >= 2

    def test_analyze_modules_root_file(self, analyzer):
        files = [{"relative_path": "setup.py", "language": "Python"}]
        result = analyzer.analyze_modules(files)
        assert "." in result["modules"]

    # --- analyze_components ---

    def test_analyze_components(self, analyzer):
        files = [{"relative_path": "src/core/engine.py"}]
        classes = [{"name": "MyService", "file_path": "src/core/engine.py"}]
        functions = [{"name": "main", "file_path": "src/core/engine.py"}]
        result = analyzer.analyze_components(files, classes, functions)
        assert "src/core" in result["components"]
        assert "MyService" in result["components"]["src/core"]["classes"]
        assert "MyService" in result["components"]["src/core"]["services"]
        assert "main" in result["components"]["src/core"]["entry_points"]

    def test_analyze_components_empty(self, analyzer):
        result = analyzer.analyze_components([], [], [])
        assert result["component_count"] == 0

    # --- analyze_dependencies ---

    def test_analyze_dependencies(self, analyzer):
        imports = [
            {"file_path": "app/services/svc.py", "module": "app.models.user"},
            {"file_path": "app/services/svc.py", "module": "app.repositories.repo"},
        ]
        files = [{"relative_path": "app/services/svc.py"}]
        result = analyzer.analyze_dependencies(imports, files)
        assert "app/services/svc.py" in result["file_dependencies"]
        assert len(result["file_dependencies"]["app/services/svc.py"]) == 2
        assert result["total_imports"] == 2

    def test_analyze_dependencies_empty(self, analyzer):
        result = analyzer.analyze_dependencies([], [])
        assert result["total_imports"] == 0

    # --- detect_circular_dependencies ---

    def test_detect_circular_simple(self, analyzer):
        deps = {"a": ["b"], "b": ["a"]}
        circular = analyzer.detect_circular_dependencies(deps)
        assert len(circular) >= 1
        assert "Circular dependency" in circular[0]["description"]

    def test_detect_circular_none(self, analyzer):
        deps = {"a": ["b"], "b": ["c"]}
        circular = analyzer.detect_circular_dependencies(deps)
        assert len(circular) == 0

    def test_detect_circular_chain(self, analyzer):
        deps = {"a": ["b"], "b": ["c"], "c": ["a"]}
        circular = analyzer.detect_circular_dependencies(deps)
        assert len(circular) >= 1

    # --- detect_layer_violations ---

    def test_detect_layer_violations(self, analyzer):
        imports = [
            {"file_path": "app/repositories/repo.py", "module": "app.api.endpoint"},
        ]
        files = [
            {"relative_path": "app/repositories/repo.py"},
            {"relative_path": "app/api/endpoint.py"},
        ]
        violations = analyzer.detect_layer_violations(imports, files)
        assert len(violations) >= 1
        assert violations[0]["violation_type"] == "layer_violation"

    def test_detect_no_layer_violations(self, analyzer):
        imports = [
            {"file_path": "app/api/endpoint.py", "module": "app.services.svc"},
        ]
        files = [
            {"relative_path": "app/api/endpoint.py"},
            {"relative_path": "app/services/svc.py"},
        ]
        violations = analyzer.detect_layer_violations(imports, files)
        assert len(violations) == 0

    def test_detect_layer_violations_util_ok(self, analyzer):
        imports = [
            {"file_path": "app/repositories/repo.py", "module": "app.utils.helper"},
        ]
        files = [
            {"relative_path": "app/repositories/repo.py"},
        ]
        violations = analyzer.detect_layer_violations(imports, files)
        assert len(violations) == 0

    # --- analyze_call_graph ---

    def test_analyze_call_graph(self, analyzer):
        functions = [
            {"name": "fn_a", "file_path": "src/main.py"},
            {"name": "fn_b", "file_path": "src/main.py"},
        ]
        methods = [
            {"name": "run", "file_path": "src/engine.py", "class_name": "Engine"},
        ]
        result = analyzer.analyze_call_graph(functions, methods)
        assert result["node_count"] == 3
        assert result["edge_count"] >= 1

    def test_analyze_call_graph_empty(self, analyzer):
        result = analyzer.analyze_call_graph([], [])
        assert result["node_count"] == 0
        assert result["edge_count"] == 0

    # --- identify_entry_points ---

    def test_identify_entry_points_files(self, analyzer):
        files = [{"relative_path": "app/main.py", "file_name": "main.py"}]
        functions = [{"name": "create_app", "file_path": "app/main.py"}]
        result = analyzer.identify_entry_points(files, functions)
        assert len(result) >= 2

    def test_identify_entry_points_empty(self, analyzer):
        result = analyzer.identify_entry_points([], [])
        assert result == []

    # --- identify_apis ---

    def test_identify_apis_file(self, analyzer):
        files = [{"relative_path": "app/api/v1/endpoints/health.py", "file_name": "health.py"}]
        functions = [{"name": "get_health", "file_path": "app/api/health.py", "decorators": "@router.get"}]
        result = analyzer.identify_apis(files, functions)
        assert len(result) >= 2

    def test_identify_apis_empty(self, analyzer):
        result = analyzer.identify_apis([], [])
        assert result == []

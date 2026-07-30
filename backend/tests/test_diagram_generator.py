"""Unit tests for DiagramGenerator."""
import json
import pytest
from app.engines.architecture_engine.diagram_generator import DiagramGenerator


class TestDiagramGenerator:

    @pytest.fixture
    def gen(self):
        return DiagramGenerator()

    @pytest.fixture
    def sample_components(self):
        return {"components": {"src/core": {"classes": ["Engine", "Parser"], "functions": ["run"], "entry_points": [], "services": []}}}

    @pytest.fixture
    def sample_modules(self):
        return {"modules": {"src/core": {"files": ["engine.py"], "file_count": 1, "languages": ["Python"]}}}

    @pytest.fixture
    def sample_layers(self):
        return {"layers": {"api": ["api/health.py"], "service": ["services/svc.py"], "model": ["models/user.py"]}}

    @pytest.fixture
    def sample_deps(self):
        return {"module_dependencies": {"app/services": ["app.models", "app.repos"]}, "total_imports": 2}

    @pytest.fixture
    def sample_callgraph(self):
        return {"nodes": [{"id": "fn:main", "name": "main", "type": "function", "file_path": "main.py"}], "edges": [{"source": "main", "target": "run", "type": "intra_module"}], "node_count": 1, "edge_count": 1}

    @pytest.fixture
    def sample_files(self):
        return [{"relative_path": "src/main.py"}, {"relative_path": "src/utils/helper.py"}]

    # --- Component diagram ---

    def test_component_mermaid(self, gen, sample_components):
        result = gen.generate_component_diagram(sample_components, "mermaid")
        assert "graph TD" in result
        assert "src_core" in result

    def test_component_plantuml(self, gen, sample_components):
        result = gen.generate_component_diagram(sample_components, "plantuml")
        assert "@startuml" in result
        assert "Engine" in result

    def test_component_json(self, gen, sample_components):
        result = gen.generate_component_diagram(sample_components, "json")
        data = json.loads(result)
        assert "components" in data

    def test_component_svg(self, gen, sample_components):
        result = gen.generate_component_diagram(sample_components, "svg")
        assert "<svg" in result
        assert "2 classes" in result

    # --- Package diagram ---

    def test_package_mermaid(self, gen, sample_modules):
        result = gen.generate_package_diagram(sample_modules, "mermaid")
        assert "graph TD" in result
        assert "1 files" in result

    def test_package_plantuml(self, gen, sample_modules):
        result = gen.generate_package_diagram(sample_modules, "plantuml")
        assert "@startuml" in result

    def test_package_json(self, gen, sample_modules):
        result = gen.generate_package_diagram(sample_modules, "json")
        data = json.loads(result)
        assert "modules" in data

    def test_package_svg(self, gen, sample_modules):
        result = gen.generate_package_diagram(sample_modules, "svg")
        assert "<svg" in result

    # --- Layer diagram ---

    def test_layer_mermaid(self, gen, sample_layers):
        result = gen.generate_layer_diagram(sample_layers, "mermaid")
        assert "graph TB" in result
        assert "API" in result

    def test_layer_plantuml(self, gen, sample_layers):
        result = gen.generate_layer_diagram(sample_layers, "plantuml")
        assert "@startuml" in result
        assert "API" in result

    def test_layer_json(self, gen, sample_layers):
        result = gen.generate_layer_diagram(sample_layers, "json")
        data = json.loads(result)
        assert "layers" in data

    def test_layer_svg(self, gen, sample_layers):
        result = gen.generate_layer_diagram(sample_layers, "svg")
        assert "<svg" in result
        assert "API" in result

    # --- Dependency diagram ---

    def test_dep_mermaid(self, gen, sample_deps):
        result = gen.generate_dependency_diagram(sample_deps, "mermaid")
        assert "graph LR" in result

    def test_dep_plantuml(self, gen, sample_deps):
        result = gen.generate_dependency_diagram(sample_deps, "plantuml")
        assert "@startuml" in result

    def test_dep_json(self, gen, sample_deps):
        result = gen.generate_dependency_diagram(sample_deps, "json")
        data = json.loads(result)
        assert "module_dependencies" in data

    def test_dep_svg(self, gen, sample_deps):
        result = gen.generate_dependency_diagram(sample_deps, "svg")
        assert "<svg" in result

    # --- Call graph diagram ---

    def test_callgraph_mermaid(self, gen, sample_callgraph):
        result = gen.generate_callgraph_diagram(sample_callgraph, "mermaid")
        assert "graph LR" in result
        assert "main" in result

    def test_callgraph_plantuml(self, gen, sample_callgraph):
        result = gen.generate_callgraph_diagram(sample_callgraph, "plantuml")
        assert "@startuml" in result

    def test_callgraph_json(self, gen, sample_callgraph):
        result = gen.generate_callgraph_diagram(sample_callgraph, "json")
        data = json.loads(result)
        assert "nodes" in data

    def test_callgraph_svg(self, gen, sample_callgraph):
        result = gen.generate_callgraph_diagram(sample_callgraph, "svg")
        assert "<svg" in result

    # --- Structure diagram ---

    def test_structure_mermaid(self, gen, sample_files):
        result = gen.generate_structure_diagram(sample_files, "mermaid")
        assert "graph TD" in result

    def test_structure_plantuml(self, gen, sample_files):
        result = gen.generate_structure_diagram(sample_files, "plantuml")
        assert "@startsalt" in result

    def test_structure_json(self, gen, sample_files):
        result = gen.generate_structure_diagram(sample_files, "json")
        data = json.loads(result)
        assert "files" in data

    def test_structure_svg(self, gen, sample_files):
        result = gen.generate_structure_diagram(sample_files, "svg")
        assert "<svg" in result
        assert "Repository Structure" in result

import json
import pytest
from pathlib import Path
from app.services.repository_scanner import RepositoryScanner, IGNORED_DIRECTORIES


@pytest.fixture
def scanner():
    return RepositoryScanner()


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary repository with sample files."""
    # Python files
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "utils.py").write_text("def helper(): pass")

    # JS files
    src = tmp_path / "src"
    src.mkdir()
    (src / "index.js").write_text("console.log('hello')")
    (src / "App.tsx").write_text("export default function App() {}")

    # Config files
    pkg = {"dependencies": {"react": "^18.2.0"}, "devDependencies": {"typescript": "^5.0.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    (tmp_path / "requirements.txt").write_text("fastapi==0.109.0\n")
    (tmp_path / "README.md").write_text("# Test Project")

    # Ignored directory
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "some_lib.js").write_text("ignored")

    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "main.cpython-312.pyc").write_bytes(b"bytecode")

    return tmp_path


class TestRepositoryScanner:
    def test_scan_finds_files(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        assert result.error is None
        assert len(result.files) > 0

    def test_scan_ignores_node_modules(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        paths = [f.relative_path for f in result.files]
        assert not any("node_modules" in p for p in paths)

    def test_scan_ignores_pycache(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        paths = [f.relative_path for f in result.files]
        assert not any("__pycache__" in p for p in paths)

    def test_scan_collects_metadata(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        main_py = next((f for f in result.files if f.file_name == "main.py"), None)
        assert main_py is not None
        assert main_py.extension == ".py"
        assert main_py.language == "Python"
        assert main_py.size_bytes > 0
        assert main_py.sha256_checksum is not None
        assert len(main_py.sha256_checksum) == 64
        assert main_py.last_modified is not None

    def test_scan_detects_languages(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        assert "Python" in result.language_stats
        assert "JavaScript" in result.language_stats
        assert result.language_stats["Python"]["file_count"] >= 2

    def test_scan_detects_frameworks(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        names = [fw.name for fw in result.frameworks]
        assert "React" in names
        assert "FastAPI" in names

    def test_scan_detects_dependencies(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        dep_names = [d.name for d in result.dependencies]
        assert "react" in dep_names
        assert "fastapi" in dep_names

    def test_scan_records_duration(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        assert result.duration_seconds > 0

    def test_scan_computes_total_size(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        assert result.total_size_bytes > 0
        assert result.total_size_bytes == sum(f.size_bytes for f in result.files)

    def test_scan_invalid_path(self, scanner):
        result = scanner.scan("/nonexistent/path")
        assert result.error is not None

    def test_language_percentages(self, scanner, tmp_repo):
        result = scanner.scan(str(tmp_repo))
        total_pct = sum(stats["percentage"] for stats in result.language_stats.values())
        # Percentages should approximately sum to 100 (some files may have no language)
        assert total_pct <= 100.1

    def test_ignored_directories_constant(self):
        assert ".git" in IGNORED_DIRECTORIES
        assert "node_modules" in IGNORED_DIRECTORIES
        assert "vendor" in IGNORED_DIRECTORIES
        assert "dist" in IGNORED_DIRECTORIES
        assert "build" in IGNORED_DIRECTORIES
        assert "target" in IGNORED_DIRECTORIES
        assert "coverage" in IGNORED_DIRECTORIES
        assert "__pycache__" in IGNORED_DIRECTORIES
        assert ".venv" in IGNORED_DIRECTORIES
        assert "venv" in IGNORED_DIRECTORIES

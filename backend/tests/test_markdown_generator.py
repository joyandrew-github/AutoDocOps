"""Unit tests for the MarkdownGenerator."""
import pytest
from app.engines.documentation_engine.markdown_generator import MarkdownGenerator


class TestMarkdownGenerator:
    """Test MarkdownGenerator document generation."""

    @pytest.fixture
    def gen(self):
        return MarkdownGenerator()

    # --- Repository overview ---

    def test_generate_repository_overview(self, gen):
        content, summary, sections = gen.generate_repository_overview(
            repo_name="MyRepo",
            description="A test repository.",
            languages=[{"name": "Python", "file_count": 10, "percentage": 80.0}],
            frameworks=[{"name": "FastAPI", "version": "0.109"}],
            dependencies=[{"name": "sqlalchemy", "version": "2.0", "package_manager": "pip"}],
            file_count=15,
            class_count=5,
            function_count=20,
        )
        assert "# MyRepo" in content
        assert "15" in content
        assert "Python" in content
        assert "FastAPI" in content
        assert "sqlalchemy" in content
        assert summary == "A test repository."
        assert len(sections) >= 3

    def test_generate_repository_overview_minimal(self, gen):
        content, summary, sections = gen.generate_repository_overview(
            repo_name="Empty", description=None,
            languages=[], frameworks=[], dependencies=[],
            file_count=0, class_count=0, function_count=0,
        )
        assert "# Empty" in content
        assert "Documentation for Empty" in summary

    # --- File documentation ---

    def test_generate_file_documentation(self, gen):
        content, summary, sections = gen.generate_file_documentation(
            file_path="src/utils.py",
            language="Python",
            classes=[{"name": "Helper", "bases": "Base", "docstring": "A helper."}],
            functions=[{"name": "process", "parameters": "x", "return_type": "int", "docstring": "Process x."}],
            imports=[{"module": "os", "name": "os"}],
            variables=[{"name": "MAX", "var_type": "int", "is_constant": True}],
        )
        assert "utils.py" in content
        assert "Helper" in content
        assert "process" in content
        assert "os" in content
        assert "MAX" in content
        assert "Python" in summary
        assert len(sections) >= 3

    def test_generate_file_documentation_empty(self, gen):
        content, summary, sections = gen.generate_file_documentation(
            file_path="empty.py", language=None,
            classes=[], functions=[], imports=[], variables=[],
        )
        assert "empty.py" in content

    # --- Class documentation ---

    def test_generate_class_documentation(self, gen):
        content, summary, sections = gen.generate_class_documentation(
            class_data={"name": "MyClass", "bases": "BaseClass", "docstring": "My class doc."},
            methods=[{"name": "run", "parameters": "self", "return_type": "None", "docstring": "Run it."}],
            file_path="models.py",
        )
        assert "MyClass" in content
        assert "BaseClass" in content
        assert "My class doc." in content
        assert "run" in content
        assert "extends" in summary

    def test_generate_class_documentation_no_methods(self, gen):
        content, summary, sections = gen.generate_class_documentation(
            class_data={"name": "Simple"}, methods=[],
        )
        assert "Simple" in content

    # --- Function documentation ---

    def test_generate_function_documentation(self, gen):
        content, summary, sections = gen.generate_function_documentation(
            func_data={"name": "calc", "parameters": "a, b", "return_type": "float", "docstring": "Calculate.", "decorators": "@cache"},
            file_path="math.py",
        )
        assert "calc" in content
        assert "a, b" in content
        assert "float" in content
        assert "Calculate." in content
        assert "@cache" in content
        assert "math.py" in content
        assert len(sections) >= 3

    def test_generate_function_documentation_minimal(self, gen):
        content, summary, sections = gen.generate_function_documentation(
            func_data={"name": "noop"},
        )
        assert "noop" in content
        assert "Function `noop`" in summary

    # --- Module documentation ---

    def test_generate_module_documentation(self, gen):
        content, summary, sections = gen.generate_module_documentation(
            module_path="src/utils",
            files=[{"file_name": "helper.py", "language": "Python"}],
            classes=[{"name": "Util", "bases": None}],
            functions=[{"name": "run", "parameters": "", "return_type": "None"}],
        )
        assert "utils" in content
        assert "helper.py" in content
        assert "Util" in content
        assert "run" in content
        assert "1 files" in summary

    def test_generate_module_documentation_empty(self, gen):
        content, summary, sections = gen.generate_module_documentation(
            module_path="empty", files=[], classes=[], functions=[],
        )
        assert "empty" in content

    # --- Changelog ---

    def test_generate_changelog(self, gen):
        content, summary, sections = gen.generate_changelog(
            repo_name="Repo",
            commits=[{"commit_hash": "abc12345", "author_name": "Alice", "committed_at": "2026-01-01", "message": "Initial commit"}],
        )
        assert "Changelog" in content
        assert "abc12345" in content
        assert "Alice" in content
        assert "1 commits" in summary

    def test_generate_changelog_empty(self, gen):
        content, summary, sections = gen.generate_changelog("Repo", [])
        assert "Changelog" in content
        assert "0 commits" in summary

    # --- Onboarding ---

    def test_generate_onboarding_guide(self, gen):
        content, summary, sections = gen.generate_onboarding_guide(
            repo_name="Repo",
            description="A project.",
            languages=[{"name": "Python"}],
            frameworks=[{"name": "FastAPI"}],
            key_files=[{"relative_path": "main.py", "file_name": "main.py"}],
        )
        assert "Onboarding" in content
        assert "A project." in content
        assert "Python" in content
        assert "main.py" in content
        assert "Getting Started" in content

    def test_generate_onboarding_no_description(self, gen):
        content, summary, sections = gen.generate_onboarding_guide(
            repo_name="X", description=None, languages=[], frameworks=[], key_files=[],
        )
        assert "Onboarding" in content

    # --- Export ---

    def test_to_html(self, gen):
        md = "# Title\n\nSome text.\n\n## Heading\n\n- item1\n- item2\n\n```python\nprint('hi')\n```\n"
        html = gen.to_html(md)
        assert "<h1>Title</h1>" in html
        assert "<h2>Heading</h2>" in html
        assert "<li>" in html
        assert "<pre><code>" in html
        assert "print('hi')" in html

    def test_to_html_table(self, gen):
        md = "| Name | Value |\n|------|-------|\n| a | 1 |\n"
        html = gen.to_html(md)
        assert "<table>" in html
        assert "<th>Name</th>" in html
        assert "<td>a</td>" in html

    def test_to_pdf_ready_markdown(self, gen):
        md = "# Doc\n\nContent."
        result = gen.to_pdf_ready_markdown(md, "My Doc")
        assert "title: \"My Doc\"" in result
        assert "output: pdf_document" in result
        assert "# Doc" in result

    # --- Private helpers ---

    def test_generate_class_section(self, gen):
        result = gen._generate_class_section({"name": "Foo", "bases": "Bar", "docstring": "A foo."})
        assert "## Foo" in result
        assert "Bar" in result
        assert "A foo." in result

    def test_generate_function_section(self, gen):
        result = gen._generate_function_section({"name": "run", "parameters": "x", "return_type": "int", "docstring": "Run it."})
        assert "## run" in result
        assert "def run(x) -> int" in result
        assert "Run it." in result

    def test_generate_method_entry(self, gen):
        result = gen._generate_method_entry({"name": "do", "parameters": "self", "return_type": "None", "docstring": "Do it."})
        assert "### do" in result
        assert "def do(self) -> None" in result
        assert "Do it." in result

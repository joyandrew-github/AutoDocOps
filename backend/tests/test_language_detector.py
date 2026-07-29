import pytest
from app.utils.language_detector import LanguageDetector


@pytest.fixture
def detector():
    return LanguageDetector()


class TestLanguageDetector:
    def test_detect_python(self, detector):
        assert detector.detect("main.py", ".py") == "Python"

    def test_detect_javascript(self, detector):
        assert detector.detect("app.js", ".js") == "JavaScript"

    def test_detect_jsx(self, detector):
        assert detector.detect("App.jsx", ".jsx") == "JavaScript"

    def test_detect_typescript(self, detector):
        assert detector.detect("index.ts", ".ts") == "TypeScript"

    def test_detect_tsx(self, detector):
        assert detector.detect("App.tsx", ".tsx") == "TypeScript"

    def test_detect_java(self, detector):
        assert detector.detect("Main.java", ".java") == "Java"

    def test_detect_go(self, detector):
        assert detector.detect("main.go", ".go") == "Go"

    def test_detect_rust(self, detector):
        assert detector.detect("main.rs", ".rs") == "Rust"

    def test_detect_c(self, detector):
        assert detector.detect("main.c", ".c") == "C"

    def test_detect_c_header(self, detector):
        assert detector.detect("header.h", ".h") == "C"

    def test_detect_cpp(self, detector):
        assert detector.detect("main.cpp", ".cpp") == "C++"

    def test_detect_csharp(self, detector):
        assert detector.detect("Program.cs", ".cs") == "C#"

    def test_detect_html(self, detector):
        assert detector.detect("index.html", ".html") == "HTML"

    def test_detect_css(self, detector):
        assert detector.detect("style.css", ".css") == "CSS"

    def test_detect_scss(self, detector):
        assert detector.detect("style.scss", ".scss") == "SCSS"

    def test_detect_yaml(self, detector):
        assert detector.detect("config.yaml", ".yaml") == "YAML"

    def test_detect_yml(self, detector):
        assert detector.detect("config.yml", ".yml") == "YAML"

    def test_detect_json(self, detector):
        assert detector.detect("data.json", ".json") == "JSON"

    def test_detect_xml(self, detector):
        assert detector.detect("pom.xml", ".xml") == "XML"

    def test_detect_markdown(self, detector):
        assert detector.detect("README.md", ".md") == "Markdown"

    def test_detect_shell(self, detector):
        assert detector.detect("setup.sh", ".sh") == "Shell"

    def test_detect_terraform(self, detector):
        assert detector.detect("main.tf", ".tf") == "Terraform"

    def test_detect_dockerfile_by_name(self, detector):
        assert detector.detect("Dockerfile", None) == "Dockerfile"

    def test_detect_makefile_by_name(self, detector):
        assert detector.detect("Makefile", None) == "Shell"

    def test_detect_unknown_extension(self, detector):
        assert detector.detect("data.xyz", ".xyz") is None

    def test_detect_no_extension(self, detector):
        assert detector.detect("somefile", None) is None

    def test_get_supported_languages(self, detector):
        languages = detector.get_supported_languages()
        assert "Python" in languages
        assert "JavaScript" in languages
        assert "TypeScript" in languages
        assert "Go" in languages
        assert "Rust" in languages
        assert "Dockerfile" in languages
        assert len(languages) > 15

import json
import os
import pytest
import tempfile
from pathlib import Path
from app.utils.framework_detector import FrameworkDetector


@pytest.fixture
def detector():
    return FrameworkDetector()


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary repository directory."""
    return tmp_path


class TestFrameworkDetector:
    def test_detect_react_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "React" in names

    def test_detect_nextjs_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"next": "14.0.0", "react": "^18.2.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Next.js" in names
        assert "React" in names

    def test_detect_angular_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"@angular/core": "^17.0.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Angular" in names

    def test_detect_vue_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"vue": "^3.3.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Vue" in names

    def test_detect_express_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"express": "^4.18.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Express" in names

    def test_detect_nestjs_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"@nestjs/core": "^10.0.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "NestJS" in names

    def test_detect_fastapi_from_requirements(self, detector, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("fastapi==0.109.0\nuvicorn==0.27.0\n")

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "FastAPI" in names

    def test_detect_flask_from_requirements(self, detector, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("Flask==3.0.0\n")

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Flask" in names

    def test_detect_django_from_requirements(self, detector, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("Django==5.0\n")

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Django" in names

    def test_detect_spring_boot_from_pom_xml(self, detector, tmp_repo):
        pom = """<project>
            <dependencies>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter</artifactId>
                </dependency>
            </dependencies>
        </project>"""
        (tmp_repo / "pom.xml").write_text(pom)

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Spring Boot" in names

    def test_detect_laravel_from_composer(self, detector, tmp_repo):
        composer = {"require": {"laravel/framework": "^10.0"}}
        (tmp_repo / "composer.json").write_text(json.dumps(composer))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Laravel" in names

    def test_detect_flutter_from_pubspec(self, detector, tmp_repo):
        pubspec = "name: myapp\ndependencies:\n  flutter:\n    sdk: flutter\n"
        (tmp_repo / "pubspec.yaml").write_text(pubspec)

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "Flutter" in names

    def test_no_frameworks_detected(self, detector, tmp_repo):
        (tmp_repo / "empty.txt").write_text("hello")
        results = detector.detect(str(tmp_repo))
        assert len(results) == 0

    def test_detect_version_from_package_json(self, detector, tmp_repo):
        pkg = {"dependencies": {"react": "^18.2.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        react = next((r for r in results if r.name == "React"), None)
        assert react is not None
        assert react.version == "18.2.0"

    def test_deduplication(self, detector, tmp_repo):
        pkg = {"dependencies": {"react": "^18.2.0"}, "devDependencies": {"react-scripts": "5.0.0"}}
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        react_count = sum(1 for r in results if r.name == "React")
        assert react_count == 1

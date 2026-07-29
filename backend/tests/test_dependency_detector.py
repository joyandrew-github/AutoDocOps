import json
import pytest
from pathlib import Path
from app.utils.dependency_detector import DependencyDetector


@pytest.fixture
def detector():
    return DependencyDetector()


@pytest.fixture
def tmp_repo(tmp_path):
    return tmp_path


class TestDependencyDetector:
    def test_detect_from_package_json(self, detector, tmp_repo):
        pkg = {
            "dependencies": {"react": "^18.2.0", "next": "14.0.0"},
            "devDependencies": {"typescript": "^5.0.0"},
        }
        (tmp_repo / "package.json").write_text(json.dumps(pkg))

        results = detector.detect(str(tmp_repo))
        assert len(results) == 3
        names = [r.name for r in results]
        assert "react" in names
        assert "next" in names
        assert "typescript" in names
        for r in results:
            assert r.package_manager == "npm"
            assert r.source_file == "package.json"

    def test_detect_from_requirements_txt(self, detector, tmp_repo):
        content = "fastapi==0.109.0\nuvicorn[standard]==0.27.0\n# comment\nsqlalchemy>=2.0.25\n"
        (tmp_repo / "requirements.txt").write_text(content)

        results = detector.detect(str(tmp_repo))
        assert len(results) == 3
        names = [r.name for r in results]
        assert "fastapi" in names
        assert "uvicorn" in names
        assert "sqlalchemy" in names
        for r in results:
            assert r.package_manager == "pip"

    def test_detect_version_from_requirements(self, detector, tmp_repo):
        (tmp_repo / "requirements.txt").write_text("fastapi==0.109.0\n")
        results = detector.detect(str(tmp_repo))
        fastapi = next((r for r in results if r.name == "fastapi"), None)
        assert fastapi is not None
        assert fastapi.version == "0.109.0"

    def test_detect_from_pom_xml(self, detector, tmp_repo):
        pom = """<project>
            <dependencies>
                <dependency>
                    <groupId>org.springframework.boot</groupId>
                    <artifactId>spring-boot-starter</artifactId>
                    <version>3.2.0</version>
                </dependency>
            </dependencies>
        </project>"""
        (tmp_repo / "pom.xml").write_text(pom)

        results = detector.detect(str(tmp_repo))
        assert len(results) == 1
        assert results[0].name == "org.springframework.boot:spring-boot-starter"
        assert results[0].version == "3.2.0"
        assert results[0].package_manager == "maven"

    def test_detect_from_build_gradle(self, detector, tmp_repo):
        gradle = """dependencies {
    implementation 'org.springframework.boot:spring-boot-starter:3.2.0'
    testImplementation 'junit:junit:4.13.2'
}"""
        (tmp_repo / "build.gradle").write_text(gradle)

        results = detector.detect(str(tmp_repo))
        assert len(results) == 2
        for r in results:
            assert r.package_manager == "gradle"

    def test_detect_from_cargo_toml(self, detector, tmp_repo):
        cargo = """[package]
name = "myapp"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }
"""
        (tmp_repo / "Cargo.toml").write_text(cargo)

        results = detector.detect(str(tmp_repo))
        assert len(results) == 2
        names = [r.name for r in results]
        assert "serde" in names
        assert "tokio" in names
        for r in results:
            assert r.package_manager == "cargo"

    def test_detect_from_go_mod(self, detector, tmp_repo):
        gomod = """module github.com/user/project

go 1.21

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/lib/pq v1.10.9
)
"""
        (tmp_repo / "go.mod").write_text(gomod)

        results = detector.detect(str(tmp_repo))
        assert len(results) == 2
        for r in results:
            assert r.package_manager == "go"

    def test_detect_from_composer_json(self, detector, tmp_repo):
        composer = {
            "require": {"php": "^8.2", "laravel/framework": "^10.0"},
            "require-dev": {"phpunit/phpunit": "^10.0"},
        }
        (tmp_repo / "composer.json").write_text(json.dumps(composer))

        results = detector.detect(str(tmp_repo))
        names = [r.name for r in results]
        assert "php" not in names  # php should be skipped
        assert "laravel/framework" in names
        assert "phpunit/phpunit" in names
        for r in results:
            assert r.package_manager == "composer"

    def test_no_dependencies_detected(self, detector, tmp_repo):
        (tmp_repo / "readme.md").write_text("hello")
        results = detector.detect(str(tmp_repo))
        assert len(results) == 0

    def test_skip_comments_in_requirements(self, detector, tmp_repo):
        content = "# this is a comment\nfastapi==0.109.0\n# another comment\n"
        (tmp_repo / "requirements.txt").write_text(content)

        results = detector.detect(str(tmp_repo))
        assert len(results) == 1
        assert results[0].name == "fastapi"

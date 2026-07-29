import json
import re
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)


class DependencyInfo:
    """Represents a detected dependency."""

    def __init__(self, name: str, version: str | None, package_manager: str, source_file: str):
        self.name = name
        self.version = version
        self.package_manager = package_manager
        self.source_file = source_file


class DependencyDetector:
    """Extracts dependencies from various package manager files."""

    DEPENDENCY_FILES: list[str] = [
        "package.json",
        "requirements.txt",
        "pyproject.toml",
        "pom.xml",
        "build.gradle",
        "Cargo.toml",
        "go.mod",
        "composer.json",
        "pubspec.yaml",
    ]

    def detect(self, repo_path: str) -> list[DependencyInfo]:
        """Detect all dependencies in the repository."""
        results: list[DependencyInfo] = []
        root = Path(repo_path)

        for dep_file in self.DEPENDENCY_FILES:
            file_path = root / dep_file
            if not file_path.exists():
                continue

            try:
                parser = self._get_parser(dep_file)
                if parser:
                    results.extend(parser(file_path))
            except Exception as e:
                logger.warning(f"Error parsing {dep_file}: {e}")

        return results

    def _get_parser(self, file_name: str):
        parsers = {
            "package.json": self._parse_package_json,
            "requirements.txt": self._parse_requirements_txt,
            "pyproject.toml": self._parse_pyproject_toml,
            "pom.xml": self._parse_pom_xml,
            "build.gradle": self._parse_build_gradle,
            "Cargo.toml": self._parse_cargo_toml,
            "go.mod": self._parse_go_mod,
            "composer.json": self._parse_composer_json,
            "pubspec.yaml": self._parse_pubspec_yaml,
        }
        return parsers.get(file_name)

    def _parse_package_json(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in ("dependencies", "devDependencies"):
            deps = data.get(section, {})
            for name, version in deps.items():
                results.append(
                    DependencyInfo(
                        name=name,
                        version=str(version).lstrip("^~>=<"),
                        package_manager="npm",
                        source_file="package.json",
                    )
                )
        return results

    def _parse_requirements_txt(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            match = re.match(r"^([a-zA-Z0-9_\-\.]+)(?:\[[^\]]*\])?\s*([><=!~]+\s*[\d\.\*]+)?", line)
            if match:
                name = match.group(1)
                version_spec = match.group(2)
                version = re.sub(r"[><=!~\s]", "", version_spec) if version_spec else None
                results.append(
                    DependencyInfo(
                        name=name,
                        version=version,
                        package_manager="pip",
                        source_file="requirements.txt",
                    )
                )
        return results

    def _parse_pyproject_toml(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        content = path.read_text(encoding="utf-8")
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "dependencies = [":
                in_deps = True
                continue
            if in_deps:
                if stripped == "]":
                    in_deps = False
                    continue
                match = re.match(r'"([a-zA-Z0-9_\-\.]+)\[?[^\]]*\]?\s*([><=!~]+\s*[\d\.\*]+)?"', stripped)
                if match:
                    name = match.group(1)
                    version_spec = match.group(2)
                    version = re.sub(r"[><=!~\s]", "", version_spec) if version_spec else None
                    results.append(
                        DependencyInfo(
                            name=name,
                            version=version,
                            package_manager="pip",
                            source_file="pyproject.toml",
                        )
                    )
        return results

    def _parse_pom_xml(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        content = path.read_text(encoding="utf-8")
        dep_pattern = re.compile(
            r"<dependency>\s*"
            r"<groupId>([^<]+)</groupId>\s*"
            r"<artifactId>([^<]+)</artifactId>\s*"
            r"(?:<version>([^<]+)</version>)?",
            re.DOTALL,
        )
        for match in dep_pattern.finditer(content):
            group_id = match.group(1)
            artifact_id = match.group(2)
            version = match.group(3)
            results.append(
                DependencyInfo(
                    name=f"{group_id}:{artifact_id}",
                    version=version,
                    package_manager="maven",
                    source_file="pom.xml",
                )
            )
        return results

    def _parse_build_gradle(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        content = path.read_text(encoding="utf-8")
        dep_pattern = re.compile(
            r"(?:implementation|api|compile|testImplementation|runtimeOnly)\s+"
            r"['\"]([^'\"]+)['\"]"
        )
        for match in dep_pattern.finditer(content):
            dep_str = match.group(1)
            parts = dep_str.split(":")
            if len(parts) >= 2:
                name = f"{parts[0]}:{parts[1]}"
                version = parts[2] if len(parts) > 2 else None
                results.append(
                    DependencyInfo(
                        name=name,
                        version=version,
                        package_manager="gradle",
                        source_file="build.gradle",
                    )
                )
        return results

    def _parse_cargo_toml(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        content = path.read_text(encoding="utf-8")
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped in ("[dependencies]", "[dev-dependencies]"):
                in_deps = True
                continue
            if stripped.startswith("[") and in_deps:
                in_deps = False
                continue
            if in_deps and "=" in stripped:
                match = re.match(r'^([a-zA-Z0-9_\-]+)\s*=\s*"?([^"]*)"?', stripped)
                if match:
                    name = match.group(1)
                    version = match.group(2).strip()
                    if version.startswith("{"):
                        ver_match = re.search(r'version\s*=\s*"([^"]+)"', version)
                        version = ver_match.group(1) if ver_match else None
                    results.append(
                        DependencyInfo(
                            name=name,
                            version=version or None,
                            package_manager="cargo",
                            source_file="Cargo.toml",
                        )
                    )
        return results

    def _parse_go_mod(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        content = path.read_text(encoding="utf-8")
        in_require = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "require (":
                in_require = True
                continue
            if stripped == ")" and in_require:
                in_require = False
                continue
            if in_require:
                parts = stripped.split()
                if len(parts) >= 2 and not parts[0].startswith("//"):
                    results.append(
                        DependencyInfo(
                            name=parts[0],
                            version=parts[1],
                            package_manager="go",
                            source_file="go.mod",
                        )
                    )
        return results

    def _parse_composer_json(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        data = json.loads(path.read_text(encoding="utf-8"))
        for section in ("require", "require-dev"):
            deps = data.get(section, {})
            for name, version in deps.items():
                if name == "php":
                    continue
                results.append(
                    DependencyInfo(
                        name=name,
                        version=str(version).lstrip("^~>=<"),
                        package_manager="composer",
                        source_file="composer.json",
                    )
                )
        return results

    def _parse_pubspec_yaml(self, path: Path) -> list[DependencyInfo]:
        results: list[DependencyInfo] = []
        content = path.read_text(encoding="utf-8")
        in_deps = False
        for line in content.splitlines():
            if line.strip() in ("dependencies:", "dev_dependencies:"):
                in_deps = True
                continue
            if in_deps and line and not line.startswith(" ") and not line.startswith("\t"):
                in_deps = False
                continue
            if in_deps:
                match = re.match(r"^\s+([a-zA-Z0-9_]+):\s*(.*)", line)
                if match:
                    name = match.group(1)
                    version = match.group(2).strip()
                    if version.startswith("^") or version.startswith("~"):
                        version = version.lstrip("^~")
                    results.append(
                        DependencyInfo(
                            name=name,
                            version=version if version else None,
                            package_manager="pub",
                            source_file="pubspec.yaml",
                        )
                    )
        return results

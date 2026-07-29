import json
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)


class FrameworkDetectionResult:
    """Result of a framework detection."""

    def __init__(self, name: str, version: str | None, confidence: str, detected_by: str):
        self.name = name
        self.version = version
        self.confidence = confidence
        self.detected_by = detected_by


class FrameworkDetector:
    """Detects frameworks by inspecting configuration files in a repository."""

    FRAMEWORK_INDICATORS: dict[str, dict] = {
        "package.json": {
            "React": {"deps": ["react"], "dev_deps": ["react-scripts"]},
            "Next.js": {"deps": ["next"]},
            "Angular": {"deps": ["@angular/core"]},
            "Vue": {"deps": ["vue"]},
            "Express": {"deps": ["express"]},
            "NestJS": {"deps": ["@nestjs/core"]},
        },
        "requirements.txt": {
            "FastAPI": {"patterns": ["fastapi"]},
            "Flask": {"patterns": ["flask", "Flask"]},
            "Django": {"patterns": ["django", "Django"]},
        },
        "pyproject.toml": {
            "FastAPI": {"patterns": ["fastapi"]},
            "Flask": {"patterns": ["flask"]},
            "Django": {"patterns": ["django"]},
        },
        "pom.xml": {
            "Spring Boot": {"patterns": ["spring-boot"]},
        },
        "build.gradle": {
            "Spring Boot": {"patterns": ["spring-boot", "org.springframework.boot"]},
        },
        "composer.json": {
            "Laravel": {"deps": ["laravel/framework"]},
        },
        "pubspec.yaml": {
            "Flutter": {"patterns": ["flutter"]},
        },
    }

    CSPROJ_FRAMEWORKS: dict[str, str] = {
        "Microsoft.AspNetCore": "ASP.NET",
        "Microsoft.NET.Sdk.Web": "ASP.NET",
    }

    def detect(self, repo_path: str) -> list[FrameworkDetectionResult]:
        """Detect all frameworks in the repository."""
        results: list[FrameworkDetectionResult] = []
        root = Path(repo_path)

        for config_file, frameworks in self.FRAMEWORK_INDICATORS.items():
            config_path = root / config_file
            if not config_path.exists():
                continue

            try:
                if config_file == "package.json":
                    results.extend(self._detect_from_package_json(config_path, frameworks))
                elif config_file in ("requirements.txt", "pyproject.toml", "pom.xml", "build.gradle"):
                    results.extend(self._detect_from_text_file(config_path, frameworks, config_file))
                elif config_file == "composer.json":
                    results.extend(self._detect_from_composer_json(config_path, frameworks))
                elif config_file == "pubspec.yaml":
                    results.extend(self._detect_from_text_file(config_path, frameworks, config_file))
            except Exception as e:
                logger.warning(f"Error inspecting {config_file}: {e}")

        # Check for .csproj files
        results.extend(self._detect_dotnet(root))

        # Deduplicate by framework name
        seen = set()
        unique: list[FrameworkDetectionResult] = []
        for r in results:
            if r.name not in seen:
                seen.add(r.name)
                unique.append(r)

        return unique

    def _detect_from_package_json(
        self, path: Path, frameworks: dict
    ) -> list[FrameworkDetectionResult]:
        results: list[FrameworkDetectionResult] = []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            all_deps = {**deps, **dev_deps}

            for framework_name, indicators in frameworks.items():
                check_deps = indicators.get("deps", [])
                check_dev_deps = indicators.get("dev_deps", [])
                for dep in check_deps + check_dev_deps:
                    if dep in all_deps:
                        version = all_deps.get(dep, "").lstrip("^~>=<")
                        results.append(
                            FrameworkDetectionResult(
                                name=framework_name,
                                version=version or None,
                                confidence="high",
                                detected_by=str(path.name),
                            )
                        )
                        break
        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")
        return results

    def _detect_from_text_file(
        self, path: Path, frameworks: dict, file_name: str
    ) -> list[FrameworkDetectionResult]:
        results: list[FrameworkDetectionResult] = []
        try:
            content = path.read_text(encoding="utf-8").lower()
            for framework_name, indicators in frameworks.items():
                patterns = indicators.get("patterns", [])
                for pattern in patterns:
                    if pattern.lower() in content:
                        results.append(
                            FrameworkDetectionResult(
                                name=framework_name,
                                version=None,
                                confidence="medium",
                                detected_by=file_name,
                            )
                        )
                        break
        except Exception as e:
            logger.warning(f"Error reading {file_name}: {e}")
        return results

    def _detect_from_composer_json(
        self, path: Path, frameworks: dict
    ) -> list[FrameworkDetectionResult]:
        results: list[FrameworkDetectionResult] = []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            require = data.get("require", {})
            for framework_name, indicators in frameworks.items():
                for dep in indicators.get("deps", []):
                    if dep in require:
                        version = require.get(dep, "").lstrip("^~>=<")
                        results.append(
                            FrameworkDetectionResult(
                                name=framework_name,
                                version=version or None,
                                confidence="high",
                                detected_by="composer.json",
                            )
                        )
                        break
        except Exception as e:
            logger.warning(f"Error parsing composer.json: {e}")
        return results

    def _detect_dotnet(self, root: Path) -> list[FrameworkDetectionResult]:
        results: list[FrameworkDetectionResult] = []
        for csproj in root.rglob("*.csproj"):
            try:
                content = csproj.read_text(encoding="utf-8")
                for indicator, framework_name in self.CSPROJ_FRAMEWORKS.items():
                    if indicator in content:
                        results.append(
                            FrameworkDetectionResult(
                                name=framework_name,
                                version=None,
                                confidence="high",
                                detected_by=csproj.name,
                            )
                        )
                        break
            except Exception as e:
                logger.warning(f"Error reading {csproj}: {e}")
        return results

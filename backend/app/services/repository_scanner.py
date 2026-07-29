import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, field
from app.utils.language_detector import LanguageDetector
from app.utils.framework_detector import FrameworkDetector, FrameworkDetectionResult
from app.utils.dependency_detector import DependencyDetector, DependencyInfo
from app.core.logging import get_logger

logger = get_logger(__name__)

IGNORED_DIRECTORIES: set[str] = {
    ".git",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "target",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}


@dataclass
class FileMetadata:
    file_name: str
    relative_path: str
    absolute_path: str
    extension: str | None
    language: str | None
    size_bytes: int
    last_modified: datetime | None
    sha256_checksum: str | None


@dataclass
class ScanResult:
    files: list[FileMetadata] = field(default_factory=list)
    language_stats: dict[str, dict] = field(default_factory=dict)
    frameworks: list[FrameworkDetectionResult] = field(default_factory=list)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    total_size_bytes: int = 0
    duration_seconds: float = 0.0
    error: str | None = None


class RepositoryScanner:
    """Recursively scans a repository and collects metadata."""

    def __init__(self):
        self.language_detector = LanguageDetector()
        self.framework_detector = FrameworkDetector()
        self.dependency_detector = DependencyDetector()

    def scan(self, repo_path: str) -> ScanResult:
        """Perform a full scan of the repository."""
        import time

        start_time = time.time()
        result = ScanResult()

        root = Path(repo_path)
        if not root.exists() or not root.is_dir():
            result.error = f"Repository path does not exist: {repo_path}"
            return result

        logger.info(f"Starting scan of repository: {repo_path}")

        # 1. Scan files
        result.files = self._scan_files(root)
        result.total_size_bytes = sum(f.size_bytes for f in result.files)
        logger.info(f"Scanned {len(result.files)} files, total size: {result.total_size_bytes} bytes")

        # 2. Compute language statistics
        result.language_stats = self._compute_language_stats(result.files, result.total_size_bytes)
        logger.info(f"Detected {len(result.language_stats)} programming languages")

        # 3. Detect frameworks
        result.frameworks = self.framework_detector.detect(repo_path)
        logger.info(f"Detected {len(result.frameworks)} frameworks")

        # 4. Detect dependencies
        result.dependencies = self.dependency_detector.detect(repo_path)
        logger.info(f"Detected {len(result.dependencies)} dependencies")

        result.duration_seconds = round(time.time() - start_time, 3)
        logger.info(f"Scan completed in {result.duration_seconds}s")

        return result

    def _scan_files(self, root: Path) -> list[FileMetadata]:
        """Recursively scan all files, skipping ignored directories."""
        files: list[FileMetadata] = []

        for dirpath, dirnames, filenames in os.walk(root):
            # Filter out ignored directories in-place
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRECTORIES]

            for filename in filenames:
                abs_path = Path(dirpath) / filename
                try:
                    metadata = self._collect_file_metadata(abs_path, root)
                    files.append(metadata)
                except Exception as e:
                    logger.warning(f"Error processing file {abs_path}: {e}")

        return files

    def _collect_file_metadata(self, abs_path: Path, root: Path) -> FileMetadata:
        """Collect metadata for a single file."""
        stat = abs_path.stat()
        relative = str(abs_path.relative_to(root))
        extension = abs_path.suffix if abs_path.suffix else None
        language = self.language_detector.detect(abs_path.name, extension)

        last_modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        checksum = self._compute_sha256(abs_path)

        return FileMetadata(
            file_name=abs_path.name,
            relative_path=relative,
            absolute_path=str(abs_path),
            extension=extension,
            language=language,
            size_bytes=stat.st_size,
            last_modified=last_modified,
            sha256_checksum=checksum,
        )

    def _compute_sha256(self, file_path: Path) -> str | None:
        """Compute SHA256 checksum of a file."""
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return None

    def _compute_language_stats(
        self, files: list[FileMetadata], total_size: int
    ) -> dict[str, dict]:
        """Compute aggregated language statistics."""
        stats: dict[str, dict] = {}
        for f in files:
            if f.language:
                if f.language not in stats:
                    stats[f.language] = {"file_count": 0, "total_size_bytes": 0}
                stats[f.language]["file_count"] += 1
                stats[f.language]["total_size_bytes"] += f.size_bytes

        # Compute percentages
        for lang, data in stats.items():
            data["percentage"] = round(
                (data["total_size_bytes"] / total_size * 100) if total_size > 0 else 0, 2
            )

        return stats

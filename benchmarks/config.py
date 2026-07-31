"""Benchmark configuration and repository profiles."""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class RepoProfile:
    """Defines a benchmark repository by size tier."""
    name: str
    url: str
    size_tier: str  # small | medium | large | xlarge
    expected_files: int = 0
    expected_functions: int = 0
    expected_classes: int = 0
    languages: list[str] = field(default_factory=list)
    description: str = ""


REPO_PROFILES: dict[str, RepoProfile] = {
    "small": RepoProfile(
        name="small-benchmark",
        url="https://github.com/pallets/click",
        size_tier="small",
        expected_files=50,
        expected_functions=200,
        expected_classes=30,
        languages=["Python"],
        description="Small CLI library (~50 files)",
    ),
    "medium": RepoProfile(
        name="medium-benchmark",
        url="https://github.com/psf/requests",
        size_tier="medium",
        expected_files=150,
        expected_functions=500,
        expected_classes=80,
        languages=["Python"],
        description="Medium HTTP library (~150 files)",
    ),
    "large": RepoProfile(
        name="large-benchmark",
        url="https://github.com/pallets/flask",
        size_tier="large",
        expected_files=300,
        expected_functions=1000,
        expected_classes=200,
        languages=["Python"],
        description="Large web framework (~300 files)",
    ),
    "xlarge": RepoProfile(
        name="xlarge-benchmark",
        url="https://github.com/django/django",
        size_tier="xlarge",
        expected_files=5000,
        expected_functions=15000,
        expected_classes=3000,
        languages=["Python"],
        description="Extra-large web framework (~5000 files)",
    ),
}


@dataclass
class BenchmarkConfig:
    """Global benchmark configuration."""
    base_url: str = os.getenv("BENCHMARK_API_URL", "http://localhost:8000")
    api_prefix: str = "/api/v1"
    output_dir: Path = Path(os.getenv("BENCHMARK_OUTPUT_DIR", "benchmarks/results"))
    repo_profiles: dict[str, RepoProfile] = field(default_factory=lambda: REPO_PROFILES)
    run_sizes: list[str] = field(default_factory=lambda: ["small"])
    timeout_seconds: int = 300
    parallel_workers: int = 4
    # AI evaluation
    ai_eval_queries: int = 20
    ai_eval_timeout: int = 60
    # Search evaluation
    search_eval_queries: int = 50
    search_relevance_threshold: float = 0.5
    # Regression detection
    regression_threshold_pct: float = 15.0  # flag if >15% slower
    # Reporting
    report_formats: list[str] = field(default_factory=lambda: ["json", "markdown", "html"])

    @property
    def url(self) -> str:
        return f"{self.base_url}{self.api_prefix}"

    def get_profile(self, size: str) -> RepoProfile:
        if size not in self.repo_profiles:
            raise ValueError(f"Unknown size tier: {size}. Available: {list(self.repo_profiles.keys())}")
        return self.repo_profiles[size]

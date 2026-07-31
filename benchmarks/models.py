"""Data models for benchmark results."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


@dataclass
class MetricResult:
    """A single measured metric."""
    name: str
    value: float
    unit: str = ""
    threshold: float | None = None
    passed: bool = True
    details: str = ""

    @property
    def is_regression(self) -> bool:
        return self.threshold is not None and self.value > self.threshold


@dataclass
class BenchmarkResult:
    """Result of a single benchmark."""
    benchmark_name: str
    category: str  # pipeline | ai | search | documentation | impact | graph | architecture | load
    repo_size: str
    duration_seconds: float = 0.0
    status: str = "pending"  # pending | running | passed | failed | error
    metrics: list[MetricResult] = field(default_factory=list)
    error: str | None = None
    started_at: str = ""
    completed_at: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def mark_start(self) -> None:
        self.status = "running"
        self.started_at = datetime.now(timezone.utc).isoformat()

    def mark_done(self, passed: bool = True) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.status = "passed" if passed else "failed"

    def mark_error(self, err: str) -> None:
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.status = "error"
        self.error = err

    def add_metric(self, name: str, value: float, unit: str = "", threshold: float | None = None, details: str = "") -> None:
        passed = True
        if threshold is not None:
            passed = value <= threshold
        self.metrics.append(MetricResult(name=name, value=value, unit=unit, threshold=threshold, passed=passed, details=details))


@dataclass
class BenchmarkSuite:
    """A complete benchmark run comprising multiple benchmarks."""
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    git_sha: str = ""
    git_branch: str = ""
    repo_sizes: list[str] = field(default_factory=list)
    results: list[BenchmarkResult] = field(default_factory=list)
    duration_seconds: float = 0.0
    environment: dict[str, str] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed(self) -> int:
        return sum(1 for r in self.results if r.status == "passed")

    @property
    def failed(self) -> int:
        return sum(1 for r in self.results if r.status == "failed")

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.status == "error")

    @property
    def pass_rate(self) -> float:
        return (self.passed / self.total * 100) if self.total else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "git_sha": self.git_sha,
            "git_branch": self.git_branch,
            "repo_sizes": self.repo_sizes,
            "duration_seconds": self.duration_seconds,
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "errors": self.errors,
                "pass_rate": round(self.pass_rate, 1),
            },
            "environment": self.environment,
            "results": [
                {
                    "benchmark_name": r.benchmark_name,
                    "category": r.category,
                    "repo_size": r.repo_size,
                    "status": r.status,
                    "duration_seconds": round(r.duration_seconds, 3),
                    "error": r.error,
                    "started_at": r.started_at,
                    "completed_at": r.completed_at,
                    "metrics": [
                        {
                            "name": m.name,
                            "value": round(m.value, 4) if isinstance(m.value, float) else m.value,
                            "unit": m.unit,
                            "threshold": m.threshold,
                            "passed": m.passed,
                            "details": m.details,
                        }
                        for m in r.metrics
                    ],
                    "details": r.details,
                }
                for r in self.results
            ],
        }

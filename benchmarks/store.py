"""Result storage — save/load benchmark suites for comparison."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from benchmarks.models import BenchmarkSuite


class ResultStore:
    """Persists benchmark results as JSON files."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, suite: BenchmarkSuite) -> Path:
        path = self.output_dir / f"run_{suite.run_id}.json"
        path.write_text(json.dumps(suite.to_dict(), indent=2), encoding="utf-8")
        # Also write a latest symlink-like file
        latest = self.output_dir / "latest.json"
        latest.write_text(json.dumps(suite.to_dict(), indent=2), encoding="utf-8")
        return path

    def load(self, run_id: str) -> dict[str, Any]:
        path = self.output_dir / f"run_{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Benchmark run not found: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def load_latest(self) -> dict[str, Any] | None:
        latest = self.output_dir / "latest.json"
        if not latest.exists():
            return None
        return json.loads(latest.read_text(encoding="utf-8"))

    def list_runs(self) -> list[dict[str, Any]]:
        runs = []
        for p in sorted(self.output_dir.glob("run_*.json"), reverse=True):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                runs.append({
                    "run_id": data["run_id"],
                    "timestamp": data["timestamp"],
                    "summary": data["summary"],
                    "git_sha": data.get("git_sha", ""),
                    "git_branch": data.get("git_branch", ""),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return runs

    def load_last_n(self, n: int = 10) -> list[dict[str, Any]]:
        runs = []
        for p in sorted(self.output_dir.glob("run_*.json"), reverse=True)[:n]:
            try:
                runs.append(json.loads(p.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return runs

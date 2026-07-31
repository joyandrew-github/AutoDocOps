"""Benchmark runner — orchestrates all benchmark suites."""
from __future__ import annotations
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

from benchmarks.config import BenchmarkConfig
from benchmarks.models import BenchmarkSuite
from benchmarks.store import ResultStore
from benchmarks.reports import generate_json_report, generate_markdown_report, generate_html_report, generate_comparison_report
from benchmarks.regression import detect_regressions, format_regression_report
from benchmarks.suites.pipeline import run_pipeline_benchmarks
from benchmarks.suites.ai_quality import run_ai_quality_benchmarks
from benchmarks.suites.search_relevance import run_search_relevance_benchmarks
from benchmarks.suites.quality import (
    run_documentation_quality_benchmarks,
    run_graph_validation_benchmarks,
    run_architecture_validation_benchmarks,
    run_impact_accuracy_benchmarks,
)
from benchmarks.suites.load_testing import run_load_benchmarks


def _git_info() -> tuple[str, str]:
    """Get current git SHA and branch."""
    sha, branch = "", ""
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        pass
    try:
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        pass
    return sha, branch


def _environment_info() -> dict[str, str]:
    return {
        "python_version": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "hostname": platform.node(),
        "ci": os.getenv("CI", "false"),
        "github_actions": os.getenv("GITHUB_ACTIONS", "false"),
    }


def run_benchmarks(
    config: BenchmarkConfig | None = None,
    sizes: list[str] | None = None,
    categories: list[str] | None = None,
) -> BenchmarkSuite:
    """Run the full benchmark suite."""
    if config is None:
        config = BenchmarkConfig()

    run_sizes = sizes or config.run_sizes
    run_categories = set(categories) if categories else None

    git_sha, git_branch = _git_info()
    suite = BenchmarkSuite(
        git_sha=git_sha,
        git_branch=git_branch,
        repo_sizes=run_sizes,
        environment=_environment_info(),
    )

    start = time.perf_counter()

    for size in run_sizes:
        profile = config.get_profile(size)
        repo_id: int | None = None

        # Pipeline benchmarks (connect, scan, parse, etc.)
        if run_categories is None or "pipeline" in run_categories:
            pipeline_results = run_pipeline_benchmarks(config, profile)
            suite.results.extend(pipeline_results)
            # Extract repo_id for subsequent suites
            for r in pipeline_results:
                if r.details.get("repository_id"):
                    repo_id = r.details["repository_id"]
                    break

        if repo_id is None:
            continue

        # AI quality
        if run_categories is None or "ai" in run_categories:
            suite.results.extend(run_ai_quality_benchmarks(config, repo_id, size))

        # Search relevance
        if run_categories is None or "search" in run_categories:
            suite.results.extend(run_search_relevance_benchmarks(config, repo_id, size))

        # Documentation quality
        if run_categories is None or "documentation" in run_categories:
            suite.results.extend(run_documentation_quality_benchmarks(config, repo_id, size))

        # Graph validation
        if run_categories is None or "graph" in run_categories:
            suite.results.extend(run_graph_validation_benchmarks(config, repo_id, size))

        # Architecture validation
        if run_categories is None or "architecture" in run_categories:
            suite.results.extend(run_architecture_validation_benchmarks(config, repo_id, size))

        # Impact accuracy
        if run_categories is None or "impact" in run_categories:
            suite.results.extend(run_impact_accuracy_benchmarks(config, repo_id, size))

        # Load testing
        if run_categories is None or "load" in run_categories:
            suite.results.extend(run_load_benchmarks(config, repo_id, size))

    suite.duration_seconds = time.perf_counter() - start

    # Store results
    store = ResultStore(config.output_dir)
    store.save(suite)

    # Generate reports
    config.output_dir.mkdir(parents=True, exist_ok=True)
    if "json" in config.report_formats:
        generate_json_report(suite, config.output_dir)
    if "markdown" in config.report_formats:
        generate_markdown_report(suite, config.output_dir)
    if "html" in config.report_formats:
        generate_html_report(suite, config.output_dir)

    # Comparison report
    historical = store.load_last_n(10)
    if len(historical) >= 2:
        generate_comparison_report(historical, config.output_dir)

    # Regression detection
    baseline = store.load_latest()
    if baseline and len(historical) >= 2:
        alerts = detect_regressions(suite.to_dict(), historical[1], config.regression_threshold_pct)
        if alerts:
            regression_md = format_regression_report(alerts)
            (config.output_dir / "regression_report.md").write_text(regression_md, encoding="utf-8")

    return suite

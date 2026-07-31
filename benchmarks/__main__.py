"""CLI entry point: python -m benchmarks [options]"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from benchmarks.config import BenchmarkConfig
from benchmarks.runner import run_benchmarks
from benchmarks.store import ResultStore
from benchmarks.reports import generate_comparison_report


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="autodocops-benchmark",
        description="AutoDocOps Evaluation & Benchmarking Framework",
    )
    sub = parser.add_subparsers(dest="command", help="Command to run")

    # run
    run_parser = sub.add_parser("run", help="Run benchmarks")
    run_parser.add_argument("--sizes", nargs="+", default=["small"], choices=["small", "medium", "large", "xlarge"], help="Repository sizes")
    run_parser.add_argument("--categories", nargs="+", default=None, help="Categories: pipeline, ai, search, documentation, graph, architecture, impact")
    run_parser.add_argument("--url", default=None, help="Backend API URL")
    run_parser.add_argument("--output", default="benchmarks/results", help="Output directory")
    run_parser.add_argument("--formats", nargs="+", default=["json", "markdown", "html"], help="Report formats")
    run_parser.add_argument("--regression-threshold", type=float, default=15.0, help="Regression threshold %%")

    # compare
    compare_parser = sub.add_parser("compare", help="Compare benchmark runs")
    compare_parser.add_argument("--last", type=int, default=5, help="Compare last N runs")
    compare_parser.add_argument("--output", default="benchmarks/results", help="Output directory")

    # list
    list_parser = sub.add_parser("list", help="List benchmark runs")
    list_parser.add_argument("--output", default="benchmarks/results", help="Output directory")

    args = parser.parse_args()

    if args.command == "run":
        config = BenchmarkConfig(
            output_dir=Path(args.output),
            run_sizes=args.sizes,
            report_formats=args.formats,
            regression_threshold_pct=args.regression_threshold,
        )
        if args.url:
            config.base_url = args.url
        print(f"Running benchmarks: sizes={args.sizes}, categories={args.categories or 'all'}")
        suite = run_benchmarks(config, categories=args.categories)
        print(f"\nCompleted in {suite.duration_seconds:.1f}s")
        print(f"  Total: {suite.total} | Passed: {suite.passed} | Failed: {suite.failed} | Errors: {suite.errors}")
        print(f"  Pass rate: {suite.pass_rate:.1f}%")
        print(f"  Run ID: {suite.run_id}")
        print(f"  Reports: {args.output}/")
        return 0 if suite.failed == 0 and suite.errors == 0 else 1

    elif args.command == "compare":
        store = ResultStore(Path(args.output))
        runs = store.load_last_n(args.last)
        if not runs:
            print("No benchmark runs found.")
            return 1
        path = generate_comparison_report(runs, Path(args.output))
        print(f"Comparison report: {path}")
        return 0

    elif args.command == "list":
        store = ResultStore(Path(args.output))
        runs = store.list_runs()
        if not runs:
            print("No benchmark runs found.")
            return 0
        print(f"{'Run ID':<14} {'Timestamp':<28} {'Pass Rate':<12} {'SHA':<10} {'Branch'}")
        print("-" * 80)
        for r in runs:
            s = r["summary"]
            print(f'{r["run_id"]:<14} {r["timestamp"][:26]:<28} {s["pass_rate"]:>5.1f}%      {r.get("git_sha","?"):<10} {r.get("git_branch","?")}')
        return 0

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())

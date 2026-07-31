"""Report generators — JSON, Markdown, HTML."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from benchmarks.models import BenchmarkSuite


def generate_json_report(suite: BenchmarkSuite, output_dir: Path) -> Path:
    path = output_dir / f"report_{suite.run_id}.json"
    path.write_text(json.dumps(suite.to_dict(), indent=2), encoding="utf-8")
    return path


def generate_markdown_report(suite: BenchmarkSuite, output_dir: Path) -> Path:
    lines: list[str] = []
    lines.append(f"# AutoDocOps Benchmark Report")
    lines.append(f"")
    lines.append(f"**Run ID:** `{suite.run_id}`  ")
    lines.append(f"**Timestamp:** {suite.timestamp}  ")
    lines.append(f"**Git SHA:** `{suite.git_sha or 'N/A'}`  ")
    lines.append(f"**Branch:** `{suite.git_branch or 'N/A'}`  ")
    lines.append(f"**Duration:** {suite.duration_seconds:.1f}s  ")
    lines.append(f"**Sizes:** {', '.join(suite.repo_sizes)}  ")
    lines.append(f"")
    lines.append(f"## Summary")
    lines.append(f"")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total | {suite.total} |")
    lines.append(f"| Passed | {suite.passed} |")
    lines.append(f"| Failed | {suite.failed} |")
    lines.append(f"| Errors | {suite.errors} |")
    lines.append(f"| Pass Rate | {suite.pass_rate:.1f}% |")
    lines.append(f"")
    lines.append(f"## Results by Category")
    lines.append(f"")

    categories: dict[str, list] = {}
    for r in suite.results:
        categories.setdefault(r.category, []).append(r)

    for cat, results in sorted(categories.items()):
        lines.append(f"### {cat.title()}")
        lines.append(f"")
        lines.append(f"| Benchmark | Size | Status | Duration | Metrics |")
        lines.append(f"|-----------|------|--------|----------|---------|")
        for r in results:
            status_icon = {"passed": "✅", "failed": "❌", "error": "⚠️"}.get(r.status, "⏳")
            metrics_summary = ", ".join(f"{m.name}={m.value:.2f}{m.unit}" for m in r.metrics[:3])
            if len(r.metrics) > 3:
                metrics_summary += f" +{len(r.metrics)-3} more"
            lines.append(f"| {r.benchmark_name} | {r.repo_size} | {status_icon} {r.status} | {r.duration_seconds:.2f}s | {metrics_summary} |")
        lines.append(f"")

    # Detailed metrics
    lines.append(f"## Detailed Metrics")
    lines.append(f"")
    for r in suite.results:
        if r.metrics:
            lines.append(f"### {r.benchmark_name} ({r.repo_size})")
            lines.append(f"")
            lines.append(f"| Metric | Value | Unit | Threshold | Status |")
            lines.append(f"|--------|-------|------|-----------|--------|")
            for m in r.metrics:
                status = "✅" if m.passed else "❌"
                thresh = f"{m.threshold}" if m.threshold is not None else "-"
                lines.append(f"| {m.name} | {m.value:.4f} | {m.unit} | {thresh} | {status} |")
            lines.append(f"")

    path = output_dir / f"report_{suite.run_id}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_html_report(suite: BenchmarkSuite, output_dir: Path) -> Path:
    data = suite.to_dict()
    categories: dict[str, list] = {}
    for r in data["results"]:
        categories.setdefault(r["category"], []).append(r)

    cat_rows = ""
    for cat, results in sorted(categories.items()):
        for r in results:
            status_cls = {"passed": "pass", "failed": "fail", "error": "error"}.get(r["status"], "")
            metrics_html = "<br>".join(f'{m["name"]}: {m["value"]}{m["unit"]}' for m in r["metrics"][:5])
            cat_rows += f'<tr class="{status_cls}"><td>{r["benchmark_name"]}</td><td>{cat}</td><td>{r["repo_size"]}</td><td>{r["status"]}</td><td>{r["duration_seconds"]:.2f}s</td><td>{metrics_html}</td></tr>\n'

    detail_sections = ""
    for r in data["results"]:
        if r["metrics"]:
            metric_rows = ""
            for m in r["metrics"]:
                cls = "pass" if m["passed"] else "fail"
                thresh = f'{m["threshold"]}' if m["threshold"] is not None else "-"
                metric_rows += f'<tr class="{cls}"><td>{m["name"]}</td><td>{m["value"]}</td><td>{m["unit"]}</td><td>{thresh}</td><td>{"✅" if m["passed"] else "❌"}</td></tr>\n'
            detail_sections += f"""
            <h3>{r["benchmark_name"]} ({r["repo_size"]})</h3>
            <table><tr><th>Metric</th><th>Value</th><th>Unit</th><th>Threshold</th><th>Status</th></tr>
            {metric_rows}</table>"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><title>AutoDocOps Benchmark Report — {data["run_id"]}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #0d1117; color: #c9d1d9; }}
h1 {{ color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 8px; }}
h2 {{ color: #58a6ff; margin-top: 32px; }}
h3 {{ color: #8b949e; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th {{ background: #161b22; color: #58a6ff; text-align: left; padding: 10px; border: 1px solid #30363d; }}
td {{ padding: 8px 10px; border: 1px solid #30363d; }}
tr:hover {{ background: #161b22; }}
tr.pass td {{ border-left: 3px solid #3fb950; }}
tr.fail td {{ border-left: 3px solid #f85149; }}
tr.error td {{ border-left: 3px solid #d29922; }}
.summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; margin: 16px 0; }}
.summary-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; text-align: center; }}
.summary-card .value {{ font-size: 2em; font-weight: bold; color: #58a6ff; }}
.summary-card .label {{ font-size: 0.85em; color: #8b949e; margin-top: 4px; }}
.meta {{ color: #8b949e; font-size: 0.9em; }}
.meta code {{ background: #161b22; padding: 2px 6px; border-radius: 4px; }}
</style></head><body>
<h1>AutoDocOps Benchmark Report</h1>
<div class="meta">
  <p>Run: <code>{data["run_id"]}</code> | Time: {data["timestamp"]} | SHA: <code>{data.get("git_sha","N/A")}</code> | Branch: <code>{data.get("git_branch","N/A")}</code> | Duration: {data["duration_seconds"]:.1f}s</p>
</div>
<div class="summary">
  <div class="summary-card"><div class="value">{data["summary"]["total"]}</div><div class="label">Total</div></div>
  <div class="summary-card"><div class="value" style="color:#3fb950">{data["summary"]["passed"]}</div><div class="label">Passed</div></div>
  <div class="summary-card"><div class="value" style="color:#f85149">{data["summary"]["failed"]}</div><div class="label">Failed</div></div>
  <div class="summary-card"><div class="value" style="color:#d29922">{data["summary"]["errors"]}</div><div class="label">Errors</div></div>
  <div class="summary-card"><div class="value">{data["summary"]["pass_rate"]}%</div><div class="label">Pass Rate</div></div>
</div>
<h2>Results</h2>
<table><tr><th>Benchmark</th><th>Category</th><th>Size</th><th>Status</th><th>Duration</th><th>Metrics</th></tr>
{cat_rows}</table>
<h2>Detailed Metrics</h2>
{detail_sections}
</body></html>"""

    path = output_dir / f"report_{suite.run_id}.html"
    path.write_text(html, encoding="utf-8")
    return path


def generate_comparison_report(runs: list[dict[str, Any]], output_dir: Path) -> Path:
    """Generate a comparison report across multiple runs."""
    if len(runs) < 2:
        return _single_run_comparison(runs, output_dir)

    lines: list[str] = []
    lines.append("# AutoDocOps Benchmark Comparison Report")
    lines.append("")
    lines.append(f"Comparing **{len(runs)}** runs:")
    lines.append("")
    for run in runs:
        lines.append(f"- `{run['run_id']}` — {run['timestamp']} (SHA: `{run.get('git_sha','?')}`)")
    lines.append("")

    # Build benchmark lookup: {name -> {run_id -> result}}
    benchmarks: dict[str, dict[str, Any]] = {}
    for run in runs:
        for r in run.get("results", []):
            key = f"{r['benchmark_name']}|{r['repo_size']}"
            benchmarks.setdefault(key, {})[run["run_id"]] = r

    lines.append("## Performance Comparison")
    lines.append("")
    run_ids = [r["run_id"] for r in runs]
    header = "| Benchmark | Size | " + " | ".join(f"`{rid[:8]}`" for rid in run_ids) + " | Trend |"
    sep = "|---|---|" + "|".join("---" for _ in run_ids) + "|---|"
    lines.append(header)
    lines.append(sep)

    for key, run_data in sorted(benchmarks.items()):
        name, size = key.split("|")
        cells = []
        durations = []
        for rid in run_ids:
            if rid in run_data:
                d = run_data[rid]["duration_seconds"]
                durations.append(d)
                cells.append(f"{d:.2f}s")
            else:
                cells.append("-")
        trend = ""
        if len(durations) >= 2:
            delta = ((durations[-1] - durations[0]) / durations[0]) * 100 if durations[0] else 0
            if delta > 15:
                trend = f"⚠️ +{delta:.0f}%"
            elif delta < -5:
                trend = f"✅ {delta:.0f}%"
            else:
                trend = f"➡️ {delta:+.0f}%"
        lines.append(f"| {name} | {size} | " + " | ".join(cells) + f" | {trend} |")

    lines.append("")

    # Metric comparison for latest two runs
    if len(runs) >= 2:
        prev, curr = runs[-2], runs[-1]
        lines.append("## Metric Deltas (Latest vs Previous)")
        lines.append("")
        lines.append("| Benchmark | Metric | Previous | Current | Delta |")
        lines.append("|---|---|---|---|---|")
        prev_map = {f'{r["benchmark_name"]}|{r["repo_size"]}': r for r in prev.get("results", [])}
        for r in curr.get("results", []):
            key = f'{r["benchmark_name"]}|{r["repo_size"]}'
            pr = prev_map.get(key)
            if not pr:
                continue
            prev_metrics = {m["name"]: m["value"] for m in pr.get("metrics", [])}
            for m in r.get("metrics", []):
                pv = prev_metrics.get(m["name"])
                if pv is not None:
                    delta = m["value"] - pv
                    pct = (delta / pv * 100) if pv else 0
                    icon = "⚠️" if pct > 15 else ("✅" if pct < -5 else "")
                    lines.append(f'| {r["benchmark_name"]} | {m["name"]} | {pv:.4f} | {m["value"]:.4f} | {icon} {delta:+.4f} ({pct:+.1f}%) |')
        lines.append("")

    path = output_dir / "comparison_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _single_run_comparison(runs: list[dict], output_dir: Path) -> Path:
    lines = ["# AutoDocOps Benchmark Comparison", "", "Not enough runs to compare (need ≥2).", ""]
    if runs:
        lines.append(f"Latest run: `{runs[0]['run_id']}` — pass rate: {runs[0]['summary']['pass_rate']}%")
    path = output_dir / "comparison_report.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

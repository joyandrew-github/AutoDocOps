"""Performance regression detection — compare current run against baseline."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class RegressionAlert:
    benchmark: str
    metric: str
    baseline_value: float
    current_value: float
    delta_pct: float
    severity: str  # info | warning | critical


def detect_regressions(
    current: dict[str, Any],
    baseline: dict[str, Any],
    threshold_pct: float = 15.0,
    critical_pct: float = 30.0,
) -> list[RegressionAlert]:
    """Compare current run against baseline, flag regressions."""
    alerts: list[RegressionAlert] = []

    baseline_map: dict[str, dict[str, float]] = {}
    for r in baseline.get("results", []):
        key = f'{r["benchmark_name"]}|{r["repo_size"]}'
        metrics = {m["name"]: m["value"] for m in r.get("metrics", [])}
        # Also track duration
        metrics["_duration"] = r.get("duration_seconds", 0)
        baseline_map[key] = metrics

    for r in current.get("results", []):
        key = f'{r["benchmark_name"]}|{r["repo_size"]}'
        bl = baseline_map.get(key)
        if not bl:
            continue

        # Check duration regression
        curr_dur = r.get("duration_seconds", 0)
        base_dur = bl.get("_duration", 0)
        if base_dur > 0 and curr_dur > 0:
            delta = ((curr_dur - base_dur) / base_dur) * 100
            if delta > critical_pct:
                alerts.append(RegressionAlert(
                    benchmark=key, metric="duration", baseline_value=base_dur,
                    current_value=curr_dur, delta_pct=delta, severity="critical",
                ))
            elif delta > threshold_pct:
                alerts.append(RegressionAlert(
                    benchmark=key, metric="duration", baseline_value=base_dur,
                    current_value=curr_dur, delta_pct=delta, severity="warning",
                ))

        # Check metric regressions (higher = worse for time-based, lower = worse for quality)
        time_metrics = {"response_time", "avg_response_time", "_duration"}
        quality_metrics = {"keyword_coverage", "quality_score", "precision_at_5", "mrr",
                          "avg_keyword_coverage", "avg_quality_score", "avg_precision_at_5",
                          "completeness", "type_coverage", "avg_mrr"}

        for m in r.get("metrics", []):
            name = m["name"]
            curr_val = m["value"]
            base_val = bl.get(name)
            if base_val is None or base_val == 0:
                continue

            if name in time_metrics:
                # Higher is worse
                delta = ((curr_val - base_val) / base_val) * 100
                if delta > critical_pct:
                    alerts.append(RegressionAlert(
                        benchmark=key, metric=name, baseline_value=base_val,
                        current_value=curr_val, delta_pct=delta, severity="critical",
                    ))
                elif delta > threshold_pct:
                    alerts.append(RegressionAlert(
                        benchmark=key, metric=name, baseline_value=base_val,
                        current_value=curr_val, delta_pct=delta, severity="warning",
                    ))
            elif name in quality_metrics:
                # Lower is worse
                delta = ((base_val - curr_val) / base_val) * 100
                if delta > critical_pct:
                    alerts.append(RegressionAlert(
                        benchmark=key, metric=name, baseline_value=base_val,
                        current_value=curr_val, delta_pct=-delta, severity="critical",
                    ))
                elif delta > threshold_pct:
                    alerts.append(RegressionAlert(
                        benchmark=key, metric=name, baseline_value=base_val,
                        current_value=curr_val, delta_pct=-delta, severity="warning",
                    ))

    return alerts


def format_regression_report(alerts: list[RegressionAlert]) -> str:
    """Format regression alerts as markdown."""
    if not alerts:
        return "## Regression Report\n\nNo regressions detected. ✅\n"

    lines = ["## Regression Report", ""]
    critical = [a for a in alerts if a.severity == "critical"]
    warnings = [a for a in alerts if a.severity == "warning"]

    if critical:
        lines.append(f"### 🔴 Critical Regressions ({len(critical)})")
        lines.append("")
        lines.append("| Benchmark | Metric | Baseline | Current | Delta |")
        lines.append("|---|---|---|---|---|")
        for a in critical:
            lines.append(f"| {a.benchmark} | {a.metric} | {a.baseline_value:.4f} | {a.current_value:.4f} | {a.delta_pct:+.1f}% |")
        lines.append("")

    if warnings:
        lines.append(f"### 🟡 Warnings ({len(warnings)})")
        lines.append("")
        lines.append("| Benchmark | Metric | Baseline | Current | Delta |")
        lines.append("|---|---|---|---|---|")
        for a in warnings:
            lines.append(f"| {a.benchmark} | {a.metric} | {a.baseline_value:.4f} | {a.current_value:.4f} | {a.delta_pct:+.1f}% |")
        lines.append("")

    return "\n".join(lines)

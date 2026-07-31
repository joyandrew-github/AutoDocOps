"""Documentation quality, knowledge graph validation, architecture validation, impact accuracy benchmarks."""
from __future__ import annotations
from benchmarks.config import BenchmarkConfig
from benchmarks.models import BenchmarkResult
from benchmarks.http_client import BenchmarkHttpClient


# ---------------------------------------------------------------------------
# Documentation Quality
# ---------------------------------------------------------------------------

def _doc_completeness(docs: list[dict]) -> float:
    """Fraction of docs that have non-empty content and summary."""
    if not docs:
        return 0.0
    complete = sum(1 for d in docs if d.get("summary") and d.get("title"))
    return complete / len(docs)


def _doc_coverage(docs: list[dict], expected_types: list[str]) -> float:
    """Fraction of expected doc types that exist."""
    if not expected_types:
        return 1.0
    found_types = {d.get("doc_type", "").lower() for d in docs}
    matched = sum(1 for t in expected_types if t.lower() in found_types)
    return matched / len(expected_types)


def run_documentation_quality_benchmarks(config: BenchmarkConfig, repo_id: int, repo_size: str = "small") -> list[BenchmarkResult]:
    client = BenchmarkHttpClient(config.url, timeout=60)
    results: list[BenchmarkResult] = []

    result = BenchmarkResult("doc_quality", "documentation", repo_size)
    result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/documentation")
        result.duration_seconds = resp["duration"]
        if resp["ok"]:
            docs = resp["data"] if isinstance(resp["data"], list) else []
            completeness = _doc_completeness(docs)
            coverage = _doc_coverage(docs, ["overview", "api", "module", "class", "function"])
            result.add_metric("total_docs", float(len(docs)), "docs")
            result.add_metric("completeness", completeness, "", threshold=0.5)
            result.add_metric("type_coverage", coverage, "")
            result.add_metric("response_time", resp["duration"], "s", threshold=5.0)
            result.mark_done(completeness >= 0.5)
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    results.append(result)

    # Search documentation
    search_result = BenchmarkResult("doc_search_quality", "documentation", repo_size)
    search_result.mark_start()
    try:
        resp = client.timed_get(f"/documentation/search?query=api+endpoint&repository_id={repo_id}")
        search_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            docs = resp["data"] if isinstance(resp["data"], list) else []
            search_result.add_metric("search_results", float(len(docs)), "docs")
            search_result.add_metric("response_time", resp["duration"], "s", threshold=3.0)
            search_result.mark_done()
        else:
            search_result.mark_error(str(resp["data"]))
    except Exception as e:
        search_result.mark_error(str(e))
    results.append(search_result)

    return results


# ---------------------------------------------------------------------------
# Knowledge Graph Validation
# ---------------------------------------------------------------------------

def run_graph_validation_benchmarks(config: BenchmarkConfig, repo_id: int, repo_size: str = "small") -> list[BenchmarkResult]:
    client = BenchmarkHttpClient(config.url, timeout=60)
    results: list[BenchmarkResult] = []

    # Statistics validation
    stats_result = BenchmarkResult("graph_statistics", "graph", repo_size)
    stats_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/graph/statistics")
        stats_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            data = resp["data"]
            total_nodes = sum(v for k, v in data.items() if isinstance(v, (int, float)) and "count" in k.lower()) or data.get("total_nodes", 0)
            total_rels = data.get("total_relationships", 0)
            stats_result.add_metric("total_nodes", float(total_nodes), "nodes")
            stats_result.add_metric("total_relationships", float(total_rels), "rels")
            stats_result.add_metric("response_time", resp["duration"], "s", threshold=3.0)
            stats_result.mark_done(True)
        else:
            stats_result.mark_error(str(resp["data"]))
    except Exception as e:
        stats_result.mark_error(str(e))
    results.append(stats_result)

    # Connected files analytics
    conn_result = BenchmarkResult("graph_connected_files", "graph", repo_size)
    conn_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/graph/analytics/connected-files?limit=10")
        conn_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            data = resp["data"] if isinstance(resp["data"], list) else []
            conn_result.add_metric("connected_files_returned", float(len(data)), "files")
            conn_result.add_metric("response_time", resp["duration"], "s", threshold=5.0)
            conn_result.mark_done()
        else:
            conn_result.mark_error(str(resp["data"]))
    except Exception as e:
        conn_result.mark_error(str(e))
    results.append(conn_result)

    # Language statistics
    lang_result = BenchmarkResult("graph_languages", "graph", repo_size)
    lang_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/graph/analytics/languages")
        lang_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            data = resp["data"] if isinstance(resp["data"], list) else []
            lang_result.add_metric("languages_detected", float(len(data)), "langs")
            lang_result.add_metric("response_time", resp["duration"], "s", threshold=3.0)
            lang_result.mark_done(len(data) > 0)
        else:
            lang_result.mark_error(str(resp["data"]))
    except Exception as e:
        lang_result.mark_error(str(e))
    results.append(lang_result)

    return results


# ---------------------------------------------------------------------------
# Architecture Validation
# ---------------------------------------------------------------------------

def run_architecture_validation_benchmarks(config: BenchmarkConfig, repo_id: int, repo_size: str = "small") -> list[BenchmarkResult]:
    client = BenchmarkHttpClient(config.url, timeout=60)
    results: list[BenchmarkResult] = []

    # List models
    list_result = BenchmarkResult("arch_models_list", "architecture", repo_size)
    list_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/architecture")
        list_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            models = resp["data"] if isinstance(resp["data"], list) else []
            list_result.add_metric("models_count", float(len(models)), "models")
            list_result.add_metric("response_time", resp["duration"], "s", threshold=3.0)
            list_result.details["model_ids"] = [m.get("id") for m in models]
            list_result.mark_done()
        else:
            list_result.mark_error(str(resp["data"]))
    except Exception as e:
        list_result.mark_error(str(e))
    results.append(list_result)

    # Dependencies
    deps_result = BenchmarkResult("arch_dependencies", "architecture", repo_size)
    deps_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/architecture/dependencies")
        deps_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            data = resp["data"] if isinstance(resp["data"], dict) else {}
            nodes = len(data.get("nodes", []))
            edges = len(data.get("edges", []))
            deps_result.add_metric("dep_nodes", float(nodes), "nodes")
            deps_result.add_metric("dep_edges", float(edges), "edges")
            deps_result.add_metric("response_time", resp["duration"], "s", threshold=5.0)
            deps_result.mark_done()
        else:
            deps_result.mark_error(str(resp["data"]))
    except Exception as e:
        deps_result.mark_error(str(e))
    results.append(deps_result)

    return results


# ---------------------------------------------------------------------------
# Impact Analysis Accuracy
# ---------------------------------------------------------------------------

def run_impact_accuracy_benchmarks(config: BenchmarkConfig, repo_id: int, repo_size: str = "small") -> list[BenchmarkResult]:
    client = BenchmarkHttpClient(config.url, timeout=60)
    results: list[BenchmarkResult] = []

    # History check
    hist_result = BenchmarkResult("impact_history", "impact", repo_size)
    hist_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/impact/history?limit=10")
        hist_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            data = resp["data"] if isinstance(resp["data"], list) else []
            hist_result.add_metric("analyses_count", float(len(data)), "analyses")
            hist_result.add_metric("response_time", resp["duration"], "s", threshold=3.0)
            # Validate data integrity
            for item in data:
                if item.get("total_changes") is not None and item.get("total_affected") is not None:
                    if item["total_affected"] > item["total_changes"] * 100:
                        hist_result.add_metric("suspicious_ratio", float(item["total_affected"] / max(item["total_changes"], 1)), "ratio")
            hist_result.mark_done()
        else:
            hist_result.mark_error(str(resp["data"]))
    except Exception as e:
        hist_result.mark_error(str(e))
    results.append(hist_result)

    # Risk assessment
    risk_result = BenchmarkResult("impact_risk", "impact", repo_size)
    risk_result.mark_start()
    try:
        resp = client.timed_get(f"/repositories/{repo_id}/impact/risk")
        risk_result.duration_seconds = resp["duration"]
        if resp["ok"]:
            data = resp["data"] if isinstance(resp["data"], dict) else {}
            risk_level = data.get("risk_level", "unknown")
            risk_score = data.get("risk_score", 0)
            risk_result.add_metric("risk_score", float(risk_score), "")
            risk_result.add_metric("response_time", resp["duration"], "s", threshold=3.0)
            risk_result.details["risk_level"] = risk_level
            # Validate score is in range
            valid_score = 0.0 <= float(risk_score) <= 100.0 if risk_score is not None else True
            risk_result.mark_done(valid_score)
        else:
            # 404 is acceptable if no analysis has been run
            if resp["status"] == 404:
                risk_result.mark_done()
                risk_result.details["note"] = "No risk assessment available (expected if no analysis run)"
            else:
                risk_result.mark_error(str(resp["data"]))
    except Exception as e:
        risk_result.mark_error(str(e))
    results.append(risk_result)

    return results

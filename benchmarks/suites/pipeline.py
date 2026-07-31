"""End-to-end pipeline benchmarks — connect, scan, parse, graph, embed, docs, architecture, impact."""
from __future__ import annotations
import time
from benchmarks.config import BenchmarkConfig, RepoProfile
from benchmarks.models import BenchmarkResult
from benchmarks.http_client import BenchmarkHttpClient


def _connect_repo(client: BenchmarkHttpClient, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("repo_connect", "pipeline", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post("/repositories/connect", {"repository_url": profile.url})
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=60.0)
        if resp["ok"]:
            result.details["repository_id"] = resp["data"].get("id")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _scan_repo(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("repo_scan", "pipeline", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/scan")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=120.0)
        if resp["ok"]:
            data = resp["data"]
            result.add_metric("total_files", float(data.get("total_files", 0)), "files")
            result.add_metric("total_languages", float(data.get("total_languages", 0)), "langs")
            result.details["scan_data"] = data
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _parse_repo(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("repo_parse", "pipeline", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/parse")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=180.0)
        if resp["ok"]:
            data = resp["data"]
            pr = data.get("parser_run", {})
            files_parsed = pr.get("total_files_parsed", 0)
            nodes = pr.get("total_nodes_extracted", 0)
            result.add_metric("files_parsed", float(files_parsed), "files")
            result.add_metric("nodes_extracted", float(nodes), "nodes")
            if files_parsed > 0:
                result.add_metric("nodes_per_file", float(nodes / files_parsed), "nodes/file")
                result.add_metric("parse_throughput", float(files_parsed / resp["duration"]) if resp["duration"] > 0 else 0, "files/s")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _sync_graph(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("graph_sync", "graph", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/graph/sync")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=120.0)
        if resp["ok"]:
            data = resp["data"]
            result.add_metric("nodes_created", float(data.get("nodes_created", 0)), "nodes")
            result.add_metric("relationships_created", float(data.get("relationships_created", 0)), "rels")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _sync_embeddings(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("embedding_sync", "search", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/embeddings/sync")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=300.0)
        if resp["ok"]:
            data = resp["data"]
            result.add_metric("embeddings_created", float(data.get("embeddings_created", 0)), "embeddings")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _generate_docs(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("doc_generation", "documentation", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/documentation/generate")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=300.0)
        if resp["ok"]:
            data = resp["data"]
            result.add_metric("docs_generated", float(data.get("documents_generated", 0)), "docs")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _generate_architecture(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("arch_generation", "architecture", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/architecture/generate")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=300.0)
        if resp["ok"]:
            data = resp["data"]
            result.add_metric("models_generated", float(data.get("models_generated", 0)), "models")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _analyze_impact(client: BenchmarkHttpClient, repo_id: int, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("impact_analysis", "impact", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_post(f"/repositories/{repo_id}/impact/analyze")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=120.0)
        if resp["ok"]:
            data = resp["data"]
            result.add_metric("total_changes", float(data.get("total_changes", 0)), "changes")
            result.add_metric("total_affected", float(data.get("total_affected", 0)), "affected")
            result.mark_done()
        else:
            result.mark_error(str(resp["data"]))
    except Exception as e:
        result.mark_error(str(e))
    return result


def _health_check(client: BenchmarkHttpClient, profile: RepoProfile) -> BenchmarkResult:
    result = BenchmarkResult("health_check", "pipeline", profile.size_tier)
    result.mark_start()
    try:
        resp = client.timed_get("/health")
        result.duration_seconds = resp["duration"]
        result.add_metric("response_time", resp["duration"], "s", threshold=2.0)
        if resp["ok"]:
            result.mark_done()
        else:
            result.mark_error("Health check failed")
    except Exception as e:
        result.mark_error(str(e))
    return result


def run_pipeline_benchmarks(config: BenchmarkConfig, profile: RepoProfile) -> list[BenchmarkResult]:
    """Run the full pipeline benchmark for a given repository profile."""
    client = BenchmarkHttpClient(config.url, timeout=config.timeout_seconds)
    results: list[BenchmarkResult] = []

    # Health check
    results.append(_health_check(client, profile))

    # Connect
    connect_result = _connect_repo(client, profile)
    results.append(connect_result)
    repo_id = connect_result.details.get("repository_id")
    if not repo_id:
        return results

    # Scan
    results.append(_scan_repo(client, repo_id, profile))
    # Parse
    results.append(_parse_repo(client, repo_id, profile))
    # Graph
    results.append(_sync_graph(client, repo_id, profile))
    # Embeddings
    results.append(_sync_embeddings(client, repo_id, profile))
    # Documentation
    results.append(_generate_docs(client, repo_id, profile))
    # Architecture
    results.append(_generate_architecture(client, repo_id, profile))
    # Impact
    results.append(_analyze_impact(client, repo_id, profile))

    return results

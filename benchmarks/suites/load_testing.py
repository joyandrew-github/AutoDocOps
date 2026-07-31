"""Load testing benchmarks — measures throughput and latency under concurrent load."""
from __future__ import annotations
import time
import concurrent.futures
from benchmarks.config import BenchmarkConfig
from benchmarks.models import BenchmarkResult
from benchmarks.http_client import BenchmarkHttpClient


def _concurrent_health_checks(client: BenchmarkHttpClient, count: int, workers: int) -> dict:
    """Run concurrent health checks and measure latency distribution."""
    durations: list[float] = []
    errors = 0

    def _single_check() -> float | None:
        try:
            _, _, dur = client.get("/health")
            return dur
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_single_check) for _ in range(count)]
        for f in concurrent.futures.as_completed(futures):
            d = f.result()
            if d is not None:
                durations.append(d)
            else:
                errors += 1

    durations.sort()
    return {
        "count": count,
        "errors": errors,
        "min": min(durations) if durations else 0,
        "max": max(durations) if durations else 0,
        "mean": sum(durations) / len(durations) if durations else 0,
        "p50": durations[len(durations) // 2] if durations else 0,
        "p95": durations[int(len(durations) * 0.95)] if durations else 0,
        "p99": durations[int(len(durations) * 0.99)] if durations else 0,
        "rps": len(durations) / sum(durations) if sum(durations) > 0 else 0,
    }


def _concurrent_search(client: BenchmarkHttpClient, repo_id: int | None, queries: list[str], workers: int) -> dict:
    """Run concurrent search requests."""
    durations: list[float] = []
    errors = 0

    def _single_search(query: str) -> float | None:
        try:
            _, _, dur = client.post("/search", {"query": query, "repository_id": repo_id, "top_k": 5})
            return dur
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_single_search, q) for q in queries]
        for f in concurrent.futures.as_completed(futures):
            d = f.result()
            if d is not None:
                durations.append(d)
            else:
                errors += 1

    durations.sort()
    return {
        "count": len(queries),
        "errors": errors,
        "min": min(durations) if durations else 0,
        "max": max(durations) if durations else 0,
        "mean": sum(durations) / len(durations) if durations else 0,
        "p50": durations[len(durations) // 2] if durations else 0,
        "p95": durations[int(len(durations) * 0.95)] if durations else 0,
        "p99": durations[int(len(durations) * 0.99)] if durations else 0,
        "rps": len(durations) / sum(durations) if sum(durations) > 0 else 0,
    }


def _concurrent_ai_chat(client: BenchmarkHttpClient, repo_id: int | None, messages: list[str], workers: int) -> dict:
    """Run concurrent AI chat requests."""
    durations: list[float] = []
    errors = 0

    def _single_chat(msg: str) -> float | None:
        try:
            _, _, dur = client.post("/ai/chat", {"message": msg, "repository_id": repo_id})
            return dur
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_single_chat, m) for m in messages]
        for f in concurrent.futures.as_completed(futures):
            d = f.result()
            if d is not None:
                durations.append(d)
            else:
                errors += 1

    durations.sort()
    return {
        "count": len(messages),
        "errors": errors,
        "min": min(durations) if durations else 0,
        "max": max(durations) if durations else 0,
        "mean": sum(durations) / len(durations) if durations else 0,
        "p50": durations[len(durations) // 2] if durations else 0,
        "p95": durations[int(len(durations) * 0.95)] if durations else 0,
        "p99": durations[int(len(durations) * 0.99)] if durations else 0,
        "rps": len(durations) / sum(durations) if sum(durations) > 0 else 0,
    }


def run_load_benchmarks(config: BenchmarkConfig, repo_id: int | None = None, repo_size: str = "small") -> list[BenchmarkResult]:
    """Run load testing benchmarks."""
    client = BenchmarkHttpClient(config.url, timeout=config.timeout_seconds)
    results: list[BenchmarkResult] = []
    workers = config.parallel_workers

    # Health check load test
    health_result = BenchmarkResult("load_health_check", "load", repo_size)
    health_result.mark_start()
    try:
        stats = _concurrent_health_checks(client, count=100, workers=workers)
        health_result.add_metric("rps", stats["rps"], "req/s")
        health_result.add_metric("p50_latency", stats["p50"], "s", threshold=0.5)
        health_result.add_metric("p95_latency", stats["p95"], "s", threshold=2.0)
        health_result.add_metric("p99_latency", stats["p99"], "s", threshold=5.0)
        health_result.add_metric("error_rate", float(stats["errors"] / stats["count"]), "", threshold=0.05)
        health_result.add_metric("mean_latency", stats["mean"], "s")
        health_result.duration_seconds = stats["mean"] * stats["count"] / workers
        health_result.details["stats"] = stats
        health_result.mark_done(stats["errors"] / stats["count"] < 0.05)
    except Exception as e:
        health_result.mark_error(str(e))
    results.append(health_result)

    # Search load test
    search_queries = ["authentication", "database connection", "error handling", "API routes", "configuration",
                      "middleware", "testing", "deployment", "logging", "caching"] * 3
    search_result = BenchmarkResult("load_search", "load", repo_size)
    search_result.mark_start()
    try:
        stats = _concurrent_search(client, repo_id, search_queries, workers)
        search_result.add_metric("rps", stats["rps"], "req/s")
        search_result.add_metric("p50_latency", stats["p50"], "s", threshold=3.0)
        search_result.add_metric("p95_latency", stats["p95"], "s", threshold=10.0)
        search_result.add_metric("error_rate", float(stats["errors"] / max(stats["count"], 1)), "", threshold=0.1)
        search_result.add_metric("mean_latency", stats["mean"], "s")
        search_result.duration_seconds = stats["mean"] * stats["count"] / workers
        search_result.details["stats"] = stats
        search_result.mark_done(stats["errors"] / max(stats["count"], 1) < 0.1)
    except Exception as e:
        search_result.mark_error(str(e))
    results.append(search_result)

    # AI chat load test (fewer requests since AI is heavier)
    ai_messages = ["explain this code", "what does this function do", "show me the architecture",
                   "find security issues", "list dependencies"] * 2
    ai_result = BenchmarkResult("load_ai_chat", "load", repo_size)
    ai_result.mark_start()
    try:
        stats = _concurrent_ai_chat(client, repo_id, ai_messages, max(workers // 2, 1))
        ai_result.add_metric("rps", stats["rps"], "req/s")
        ai_result.add_metric("p50_latency", stats["p50"], "s", threshold=30.0)
        ai_result.add_metric("p95_latency", stats["p95"], "s", threshold=60.0)
        ai_result.add_metric("error_rate", float(stats["errors"] / max(stats["count"], 1)), "", threshold=0.2)
        ai_result.add_metric("mean_latency", stats["mean"], "s")
        ai_result.duration_seconds = stats["mean"] * stats["count"] / max(workers // 2, 1)
        ai_result.details["stats"] = stats
        ai_result.mark_done(stats["errors"] / max(stats["count"], 1) < 0.2)
    except Exception as e:
        ai_result.mark_error(str(e))
    results.append(ai_result)

    return results

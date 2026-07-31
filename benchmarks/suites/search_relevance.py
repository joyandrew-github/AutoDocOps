"""Search relevance evaluation benchmarks."""
from __future__ import annotations
from benchmarks.config import BenchmarkConfig
from benchmarks.models import BenchmarkResult
from benchmarks.http_client import BenchmarkHttpClient

SEARCH_EVAL_QUERIES = [
    {"query": "authentication login handler", "expected_types": ["function", "class"], "expected_terms": ["auth", "login"]},
    {"query": "database connection setup", "expected_types": ["function", "class"], "expected_terms": ["database", "connection", "session", "db"]},
    {"query": "error handling middleware", "expected_types": ["function", "class"], "expected_terms": ["error", "exception", "handler", "middleware"]},
    {"query": "API route definition", "expected_types": ["function"], "expected_terms": ["route", "router", "endpoint", "api"]},
    {"query": "configuration settings", "expected_types": ["class", "variable"], "expected_terms": ["config", "setting", "env"]},
    {"query": "data validation schema", "expected_types": ["class"], "expected_terms": ["schema", "model", "valid", "pydantic"]},
    {"query": "file parser implementation", "expected_types": ["function", "class"], "expected_terms": ["parse", "file", "ast", "tree"]},
    {"query": "caching mechanism", "expected_types": ["function", "class"], "expected_terms": ["cache", "redis", "get", "set"]},
    {"query": "background task worker", "expected_types": ["function"], "expected_terms": ["task", "worker", "celery", "queue"]},
    {"query": "logging configuration", "expected_types": ["function"], "expected_terms": ["log", "logger", "setup"]},
    {"query": "JWT token creation", "expected_types": ["function"], "expected_terms": ["token", "jwt", "create", "access"]},
    {"query": "graph database query", "expected_types": ["function", "class"], "expected_terms": ["graph", "neo4j", "query", "node"]},
    {"query": "embedding vector generation", "expected_types": ["function", "class"], "expected_terms": ["embed", "vector", "dimension"]},
    {"query": "webhook event processing", "expected_types": ["function", "class"], "expected_terms": ["webhook", "event", "handle", "payload"]},
    {"query": "documentation generator", "expected_types": ["function", "class"], "expected_terms": ["doc", "generate", "markdown"]},
    {"query": "impact analysis service", "expected_types": ["function", "class"], "expected_terms": ["impact", "analysis", "risk", "change"]},
    {"query": "architecture model builder", "expected_types": ["function", "class"], "expected_terms": ["architecture", "model", "diagram"]},
    {"query": "repository scanner", "expected_types": ["function", "class"], "expected_terms": ["scan", "repository", "file"]},
    {"query": "password hashing utility", "expected_types": ["function"], "expected_terms": ["password", "hash", "bcrypt", "verify"]},
    {"query": "rate limiting middleware", "expected_types": ["function", "class"], "expected_terms": ["rate", "limit", "throttle"]},
    {"query": "health check endpoint", "expected_types": ["function"], "expected_terms": ["health", "check", "status", "ready"]},
    {"query": "git commit history", "expected_types": ["function", "class"], "expected_terms": ["git", "commit", "history", "snapshot"]},
    {"query": "dependency graph traversal", "expected_types": ["function"], "expected_terms": ["dependency", "graph", "traverse", "import"]},
    {"query": "test fixture setup", "expected_types": ["function"], "expected_terms": ["test", "fixture", "mock", "setup"]},
    {"query": "serialization and deserialization", "expected_types": ["function", "class"], "expected_terms": ["serial", "json", "model", "schema"]},
]


def _precision_at_k(results: list[dict], expected_terms: list[str], k: int = 5) -> float:
    """Precision@K — fraction of top-K results that match expected terms."""
    if not results:
        return 0.0
    top_k = results[:k]
    relevant = 0
    for r in top_k:
        text = f"{r.get('entity_name', '')} {r.get('file_path', '')} {r.get('entity_type', '')}".lower()
        if any(t.lower() in text for t in expected_terms):
            relevant += 1
    return relevant / len(top_k)


def _mrr(results: list[dict], expected_terms: list[str]) -> float:
    """Mean Reciprocal Rank — 1/rank of first relevant result."""
    for i, r in enumerate(results):
        text = f"{r.get('entity_name', '')} {r.get('file_path', '')} {r.get('entity_type', '')}".lower()
        if any(t.lower() in text for t in expected_terms):
            return 1.0 / (i + 1)
    return 0.0


def _type_accuracy(results: list[dict], expected_types: list[str]) -> float:
    """Fraction of results matching expected entity types."""
    if not results:
        return 0.0
    matched = sum(1 for r in results if r.get("entity_type", "").lower() in [t.lower() for t in expected_types])
    return matched / len(results)


def _avg_score(results: list[dict]) -> float:
    """Average similarity score of returned results."""
    scores = [r.get("similarity_score", r.get("score", 0)) for r in results]
    return sum(scores) / len(scores) if scores else 0.0


def run_search_relevance_benchmarks(config: BenchmarkConfig, repo_id: int | None = None, repo_size: str = "small") -> list[BenchmarkResult]:
    """Evaluate search result relevance."""
    client = BenchmarkHttpClient(config.url, timeout=60)
    results: list[BenchmarkResult] = []

    queries = SEARCH_EVAL_QUERIES[:config.search_eval_queries]
    all_p5: list[float] = []
    all_mrr: list[float] = []
    all_type_acc: list[float] = []
    all_durations: list[float] = []
    errors = 0

    for q in queries:
        result = BenchmarkResult("search_relevance", "search", repo_size)
        result.mark_start()
        try:
            resp = client.timed_post("/search", {
                "query": q["query"],
                "repository_id": repo_id,
                "top_k": 10,
            })
            result.duration_seconds = resp["duration"]
            all_durations.append(resp["duration"])

            if resp["ok"] and resp["data"]:
                search_results = resp["data"].get("results", [])
                p5 = _precision_at_k(search_results, q["expected_terms"], k=5)
                mrr_val = _mrr(search_results, q["expected_terms"])
                type_acc = _type_accuracy(search_results, q["expected_types"])
                avg_sim = _avg_score(search_results)

                all_p5.append(p5)
                all_mrr.append(mrr_val)
                all_type_acc.append(type_acc)

                result.add_metric("precision_at_5", p5, "", threshold=config.search_relevance_threshold)
                result.add_metric("mrr", mrr_val, "")
                result.add_metric("type_accuracy", type_acc, "")
                result.add_metric("avg_similarity", avg_sim, "")
                result.add_metric("result_count", float(len(search_results)), "results")
                result.add_metric("response_time", resp["duration"], "s", threshold=5.0)
                result.details["query"] = q["query"]
                result.mark_done(p5 >= config.search_relevance_threshold)
            else:
                errors += 1
                result.mark_error(str(resp["data"]))
        except Exception as e:
            errors += 1
            result.mark_error(str(e))
        results.append(result)

    # Aggregate
    agg = BenchmarkResult("search_relevance_aggregate", "search", repo_size)
    agg.mark_start()
    if all_p5:
        agg.add_metric("avg_precision_at_5", sum(all_p5) / len(all_p5), "", threshold=0.4)
        agg.add_metric("avg_mrr", sum(all_mrr) / len(all_mrr), "", threshold=0.3)
        agg.add_metric("avg_type_accuracy", sum(all_type_acc) / len(all_type_acc), "")
        agg.add_metric("avg_response_time", sum(all_durations) / len(all_durations), "s")
        agg.add_metric("total_queries", float(len(queries)), "queries")
        agg.add_metric("error_rate", float(errors / len(queries)), "", threshold=0.2)
        passed = sum(all_p5) / len(all_p5) >= 0.4
        agg.mark_done(passed)
    else:
        agg.mark_error("No search results received")
    results.append(agg)

    return results

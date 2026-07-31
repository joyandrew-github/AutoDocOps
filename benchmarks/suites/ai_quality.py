"""AI response quality evaluation benchmarks."""
from __future__ import annotations
import time
from benchmarks.config import BenchmarkConfig
from benchmarks.models import BenchmarkResult
from benchmarks.http_client import BenchmarkHttpClient

AI_EVAL_QUERIES = [
    {"message": "Explain the repository structure", "expected_keywords": ["file", "module", "directory", "structure"], "category": "comprehension"},
    {"message": "What are the main entry points?", "expected_keywords": ["main", "entry", "start", "run"], "category": "comprehension"},
    {"message": "List the dependencies used", "expected_keywords": ["dependency", "package", "library", "import"], "category": "comprehension"},
    {"message": "Explain the authentication flow", "expected_keywords": ["auth", "token", "login", "password"], "category": "comprehension"},
    {"message": "What design patterns are used?", "expected_keywords": ["pattern", "factory", "singleton", "observer", "decorator"], "category": "analysis"},
    {"message": "Find potential security issues", "expected_keywords": ["security", "vulnerability", "risk", "injection", "input"], "category": "analysis"},
    {"message": "Summarize the error handling strategy", "expected_keywords": ["error", "exception", "handling", "try", "catch"], "category": "analysis"},
    {"message": "How is the database layer structured?", "expected_keywords": ["database", "model", "query", "schema", "table"], "category": "comprehension"},
    {"message": "What testing patterns are used?", "expected_keywords": ["test", "mock", "assert", "fixture", "coverage"], "category": "analysis"},
    {"message": "Explain the API routing structure", "expected_keywords": ["route", "endpoint", "api", "handler", "request"], "category": "comprehension"},
    {"message": "How is configuration managed?", "expected_keywords": ["config", "setting", "environment", "variable"], "category": "comprehension"},
    {"message": "What is the deployment strategy?", "expected_keywords": ["deploy", "docker", "container", "kubernetes", "ci"], "category": "analysis"},
    {"message": "How are background tasks handled?", "expected_keywords": ["task", "queue", "worker", "async", "celery"], "category": "comprehension"},
    {"message": "Explain the caching strategy", "expected_keywords": ["cache", "redis", "memory", "invalidate", "ttl"], "category": "analysis"},
    {"message": "What logging and monitoring is in place?", "expected_keywords": ["log", "monitor", "metric", "trace", "alert"], "category": "analysis"},
    {"message": "How are migrations managed?", "expected_keywords": ["migration", "alembic", "schema", "upgrade", "version"], "category": "comprehension"},
    {"message": "Explain the AI agent system", "expected_keywords": ["agent", "orchestrator", "ai", "llm", "model"], "category": "comprehension"},
    {"message": "How does the graph engine work?", "expected_keywords": ["graph", "neo4j", "node", "relationship", "query"], "category": "comprehension"},
    {"message": "Describe the search implementation", "expected_keywords": ["search", "embedding", "vector", "similarity", "semantic"], "category": "comprehension"},
    {"message": "What are the webhook handlers?", "expected_keywords": ["webhook", "event", "github", "push", "pull"], "category": "comprehension"},
]


def _keyword_coverage(response: str, keywords: list[str]) -> float:
    """Fraction of expected keywords found in AI response."""
    if not response:
        return 0.0
    lower = response.lower()
    found = sum(1 for kw in keywords if kw.lower() in lower)
    return found / len(keywords) if keywords else 0.0


def _response_quality_score(response: str) -> float:
    """Heuristic quality score (0-1) based on length, structure, specificity."""
    if not response:
        return 0.0
    score = 0.0
    # Length: prefer 100-2000 chars
    length = len(response)
    if length >= 50:
        score += 0.2
    if length >= 200:
        score += 0.2
    if length >= 500:
        score += 0.1
    # Structure: contains line breaks, lists, code
    if "\n" in response:
        score += 0.1
    if any(marker in response for marker in ["- ", "* ", "1.", "```"]):
        score += 0.1
    # Specificity: not too generic
    generic_phrases = ["i'm not sure", "i don't know", "i cannot", "no information"]
    if not any(gp in response.lower() for gp in generic_phrases):
        score += 0.2
    # Has some technical terms
    tech_terms = ["function", "class", "module", "file", "api", "database", "import", "return", "parameter"]
    tech_count = sum(1 for t in tech_terms if t in response.lower())
    score += min(0.1, tech_count * 0.02)
    return min(1.0, score)


def run_ai_quality_benchmarks(config: BenchmarkConfig, repo_id: int | None = None, repo_size: str = "small") -> list[BenchmarkResult]:
    """Evaluate AI response quality."""
    client = BenchmarkHttpClient(config.url, timeout=config.ai_eval_timeout)
    results: list[BenchmarkResult] = []

    queries = AI_EVAL_QUERIES[:config.ai_eval_queries]
    all_keyword_scores: list[float] = []
    all_quality_scores: list[float] = []
    all_durations: list[float] = []
    errors = 0

    for q in queries:
        result = BenchmarkResult(f"ai_quality_{q['category']}", "ai", repo_size)
        result.mark_start()
        try:
            resp = client.timed_post("/ai/chat", {
                "message": q["message"],
                "repository_id": repo_id,
            })
            result.duration_seconds = resp["duration"]
            all_durations.append(resp["duration"])

            if resp["ok"] and resp["data"]:
                content = resp["data"].get("content", "")
                kw_score = _keyword_coverage(content, q["expected_keywords"])
                quality = _response_quality_score(content)
                all_keyword_scores.append(kw_score)
                all_quality_scores.append(quality)

                result.add_metric("keyword_coverage", kw_score, "", threshold=0.3)
                result.add_metric("quality_score", quality, "", threshold=0.4)
                result.add_metric("response_time", resp["duration"], "s", threshold=float(config.ai_eval_timeout))
                result.add_metric("response_length", float(len(content)), "chars")
                result.details["query"] = q["message"]
                result.details["agent"] = resp["data"].get("agent_name", "")
                result.mark_done(kw_score >= 0.3 and quality >= 0.4)
            else:
                errors += 1
                result.mark_error(str(resp["data"]))
        except Exception as e:
            errors += 1
            result.mark_error(str(e))
        results.append(result)

    # Aggregate result
    agg = BenchmarkResult("ai_quality_aggregate", "ai", repo_size)
    agg.mark_start()
    if all_keyword_scores:
        avg_kw = sum(all_keyword_scores) / len(all_keyword_scores)
        avg_q = sum(all_quality_scores) / len(all_quality_scores)
        avg_d = sum(all_durations) / len(all_durations)
        agg.add_metric("avg_keyword_coverage", avg_kw, "", threshold=0.4)
        agg.add_metric("avg_quality_score", avg_q, "", threshold=0.5)
        agg.add_metric("avg_response_time", avg_d, "s")
        agg.add_metric("total_queries", float(len(queries)), "queries")
        agg.add_metric("error_rate", float(errors / len(queries)), "", threshold=0.2)
        agg.mark_done(avg_kw >= 0.4 and avg_q >= 0.5)
    else:
        agg.mark_error("No AI responses received")
    results.append(agg)

    return results

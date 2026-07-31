"""Tests for the benchmark framework core components."""
import json
import tempfile
from pathlib import Path

import pytest

from benchmarks.config import BenchmarkConfig, RepoProfile, REPO_PROFILES
from benchmarks.models import BenchmarkResult, BenchmarkSuite, MetricResult
from benchmarks.store import ResultStore
from benchmarks.reports import generate_json_report, generate_markdown_report, generate_html_report, generate_comparison_report
from benchmarks.regression import detect_regressions, format_regression_report, RegressionAlert


# ---- Config ----

class TestConfig:
    def test_default_config(self):
        config = BenchmarkConfig()
        assert config.base_url == "http://localhost:8000"
        assert config.api_prefix == "/api/v1"
        assert "small" in config.repo_profiles

    def test_get_profile(self):
        config = BenchmarkConfig()
        p = config.get_profile("small")
        assert p.size_tier == "small"
        assert p.name == "small-benchmark"

    def test_get_profile_invalid(self):
        config = BenchmarkConfig()
        with pytest.raises(ValueError, match="Unknown size tier"):
            config.get_profile("tiny")

    def test_url_property(self):
        config = BenchmarkConfig(base_url="http://example.com", api_prefix="/v2")
        assert config.url == "http://example.com/v2"

    def test_repo_profiles(self):
        assert "small" in REPO_PROFILES
        assert "medium" in REPO_PROFILES
        assert "large" in REPO_PROFILES
        assert "xlarge" in REPO_PROFILES


# ---- Models ----

class TestModels:
    def test_metric_result(self):
        m = MetricResult(name="latency", value=1.5, unit="s", threshold=2.0)
        assert m.passed is True
        assert m.is_regression is False

    def test_metric_regression(self):
        m = MetricResult(name="latency", value=3.0, unit="s", threshold=2.0, passed=False)
        assert m.is_regression is True

    def test_benchmark_result_lifecycle(self):
        r = BenchmarkResult("test", "pipeline", "small")
        assert r.status == "pending"
        r.mark_start()
        assert r.status == "running"
        r.add_metric("time", 1.0, "s", threshold=5.0)
        r.mark_done()
        assert r.status == "passed"
        assert len(r.metrics) == 1

    def test_benchmark_result_error(self):
        r = BenchmarkResult("test", "pipeline", "small")
        r.mark_start()
        r.mark_error("something broke")
        assert r.status == "error"
        assert r.error == "something broke"

    def test_benchmark_suite(self):
        suite = BenchmarkSuite()
        assert suite.total == 0
        assert suite.pass_rate == 0.0
        r1 = BenchmarkResult("a", "pipeline", "small", status="passed")
        r2 = BenchmarkResult("b", "pipeline", "small", status="failed")
        r3 = BenchmarkResult("c", "pipeline", "small", status="error")
        suite.results = [r1, r2, r3]
        assert suite.total == 3
        assert suite.passed == 1
        assert suite.failed == 1
        assert suite.errors == 1
        assert suite.pass_rate == pytest.approx(33.3, abs=0.1)

    def test_suite_to_dict(self):
        suite = BenchmarkSuite(git_sha="abc", git_branch="main")
        r = BenchmarkResult("test", "pipeline", "small", status="passed", duration_seconds=1.23)
        r.add_metric("time", 0.5, "s")
        suite.results = [r]
        d = suite.to_dict()
        assert d["run_id"] == suite.run_id
        assert d["git_sha"] == "abc"
        assert d["summary"]["total"] == 1
        assert len(d["results"]) == 1
        assert len(d["results"][0]["metrics"]) == 1


# ---- Store ----

class TestStore:
    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ResultStore(Path(tmp))
            suite = BenchmarkSuite(git_sha="test123")
            r = BenchmarkResult("test", "pipeline", "small", status="passed")
            suite.results = [r]
            path = store.save(suite)
            assert path.exists()
            loaded = store.load(suite.run_id)
            assert loaded["run_id"] == suite.run_id
            assert loaded["git_sha"] == "test123"

    def test_load_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ResultStore(Path(tmp))
            suite = BenchmarkSuite()
            suite.results = [BenchmarkResult("x", "pipeline", "small", status="passed")]
            store.save(suite)
            latest = store.load_latest()
            assert latest is not None
            assert latest["run_id"] == suite.run_id

    def test_load_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ResultStore(Path(tmp))
            with pytest.raises(FileNotFoundError):
                store.load("nonexistent")

    def test_list_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ResultStore(Path(tmp))
            for _ in range(3):
                suite = BenchmarkSuite()
                suite.results = [BenchmarkResult("x", "pipeline", "small", status="passed")]
                store.save(suite)
            runs = store.list_runs()
            assert len(runs) == 3

    def test_load_last_n(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = ResultStore(Path(tmp))
            for _ in range(5):
                suite = BenchmarkSuite()
                suite.results = [BenchmarkResult("x", "pipeline", "small", status="passed")]
                store.save(suite)
            last3 = store.load_last_n(3)
            assert len(last3) == 3


# ---- Reports ----

class TestReports:
    def _make_suite(self) -> BenchmarkSuite:
        suite = BenchmarkSuite(git_sha="abc123", git_branch="main", repo_sizes=["small"], duration_seconds=42.5)
        r1 = BenchmarkResult("repo_connect", "pipeline", "small", status="passed", duration_seconds=2.1)
        r1.add_metric("response_time", 2.1, "s", threshold=60.0)
        r2 = BenchmarkResult("ai_quality", "ai", "small", status="passed", duration_seconds=5.3)
        r2.add_metric("keyword_coverage", 0.75, "")
        r2.add_metric("quality_score", 0.8, "")
        r3 = BenchmarkResult("search_relevance", "search", "small", status="failed", duration_seconds=1.2)
        r3.add_metric("precision_at_5", 0.2, "", threshold=0.5)
        suite.results = [r1, r2, r3]
        return suite

    def test_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = self._make_suite()
            path = generate_json_report(suite, Path(tmp))
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["run_id"] == suite.run_id
            assert len(data["results"]) == 3

    def test_markdown_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = self._make_suite()
            path = generate_markdown_report(suite, Path(tmp))
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "# AutoDocOps Benchmark Report" in content
            assert "repo_connect" in content
            assert "ai_quality" in content

    def test_html_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = self._make_suite()
            path = generate_html_report(suite, Path(tmp))
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "<html" in content
            assert "repo_connect" in content
            assert suite.run_id in content

    def test_comparison_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            run1 = BenchmarkSuite(git_sha="aaa", repo_sizes=["small"], duration_seconds=10)
            run1.results = [BenchmarkResult("test", "pipeline", "small", status="passed", duration_seconds=1.0)]
            run1.results[0].add_metric("response_time", 1.0, "s")
            run2 = BenchmarkSuite(git_sha="bbb", repo_sizes=["small"], duration_seconds=12)
            run2.results = [BenchmarkResult("test", "pipeline", "small", status="passed", duration_seconds=1.5)]
            run2.results[0].add_metric("response_time", 1.5, "s")
            path = generate_comparison_report([run1.to_dict(), run2.to_dict()], Path(tmp))
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "Comparison" in content
            assert "aaa" in content

    def test_comparison_single_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run1 = BenchmarkSuite()
            run1.results = [BenchmarkResult("test", "pipeline", "small", status="passed")]
            path = generate_comparison_report([run1.to_dict()], Path(tmp))
            assert "Not enough runs" in path.read_text(encoding="utf-8")


# ---- Regression ----

class TestRegression:
    def test_no_regression(self):
        baseline = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.0, "metrics": [{"name": "response_time", "value": 1.0}]}]
        }
        current = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.05, "metrics": [{"name": "response_time", "value": 1.05}]}]
        }
        alerts = detect_regressions(current, baseline)
        assert len(alerts) == 0

    def test_warning_regression(self):
        baseline = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.0, "metrics": [{"name": "response_time", "value": 1.0}]}]
        }
        current = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.2, "metrics": [{"name": "response_time", "value": 1.2}]}]
        }
        alerts = detect_regressions(current, baseline, threshold_pct=15.0)
        warnings = [a for a in alerts if a.severity == "warning"]
        assert len(warnings) >= 1

    def test_critical_regression(self):
        baseline = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.0, "metrics": [{"name": "response_time", "value": 1.0}]}]
        }
        current = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 2.0, "metrics": [{"name": "response_time", "value": 2.0}]}]
        }
        alerts = detect_regressions(current, baseline, threshold_pct=15.0, critical_pct=30.0)
        critical = [a for a in alerts if a.severity == "critical"]
        assert len(critical) >= 1

    def test_quality_regression(self):
        baseline = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.0, "metrics": [{"name": "avg_quality_score", "value": 0.8}]}]
        }
        current = {
            "results": [{"benchmark_name": "test", "repo_size": "small", "duration_seconds": 1.0, "metrics": [{"name": "avg_quality_score", "value": 0.5}]}]
        }
        alerts = detect_regressions(current, baseline, threshold_pct=15.0)
        assert len(alerts) >= 1

    def test_format_no_alerts(self):
        report = format_regression_report([])
        assert "No regressions" in report

    def test_format_with_alerts(self):
        alerts = [
            RegressionAlert("test|small", "response_time", 1.0, 2.0, 100.0, "critical"),
            RegressionAlert("test|small", "duration", 1.0, 1.2, 20.0, "warning"),
        ]
        report = format_regression_report(alerts)
        assert "Critical" in report
        assert "Warning" in report


# ---- AI Quality helpers ----

class TestAIHelpers:
    def test_keyword_coverage(self):
        from benchmarks.suites.ai_quality import _keyword_coverage
        assert _keyword_coverage("This uses auth and login tokens", ["auth", "login", "token"]) == pytest.approx(1.0)
        assert _keyword_coverage("No relevant content", ["auth", "login"]) == pytest.approx(0.0)
        assert _keyword_coverage("", ["auth"]) == 0.0

    def test_response_quality_score(self):
        from benchmarks.suites.ai_quality import _response_quality_score
        assert _response_quality_score("") == 0.0
        short = "Hello"
        long_response = "This function handles authentication by verifying the JWT token.\n- Step 1: Decode token\n- Step 2: Validate claims\n```python\ndef verify():\n    pass\n```\nThe module uses bcrypt for password hashing."
        assert _response_quality_score(long_response) > _response_quality_score(short)


# ---- Search helpers ----

class TestSearchHelpers:
    def test_precision_at_k(self):
        from benchmarks.suites.search_relevance import _precision_at_k
        results = [
            {"entity_name": "login_handler", "file_path": "auth.py", "entity_type": "function"},
            {"entity_name": "get_users", "file_path": "users.py", "entity_type": "function"},
            {"entity_name": "auth_middleware", "file_path": "middleware.py", "entity_type": "function"},
        ]
        p = _precision_at_k(results, ["auth", "login"], k=3)
        assert p == pytest.approx(2.0 / 3.0, abs=0.01)

    def test_mrr(self):
        from benchmarks.suites.search_relevance import _mrr
        results = [
            {"entity_name": "unrelated", "file_path": "other.py", "entity_type": "function"},
            {"entity_name": "auth_handler", "file_path": "auth.py", "entity_type": "function"},
        ]
        assert _mrr(results, ["auth"]) == pytest.approx(0.5)
        assert _mrr([], ["auth"]) == 0.0

    def test_type_accuracy(self):
        from benchmarks.suites.search_relevance import _type_accuracy
        results = [
            {"entity_type": "function"},
            {"entity_type": "class"},
            {"entity_type": "function"},
        ]
        assert _type_accuracy(results, ["function"]) == pytest.approx(2.0 / 3.0, abs=0.01)

    def test_avg_score(self):
        from benchmarks.suites.search_relevance import _avg_score
        results = [{"similarity_score": 0.9}, {"similarity_score": 0.7}]
        assert _avg_score(results) == pytest.approx(0.8)

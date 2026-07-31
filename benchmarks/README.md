# AutoDocOps Evaluation & Benchmarking Framework

Comprehensive benchmarking framework for measuring AutoDocOps performance, quality, and reliability.

## Features

- **End-to-end pipeline benchmarks** — connect, scan, parse, graph sync, embeddings
- **Repository performance benchmarking** — small/medium/large/xlarge tiers
- **AI response quality evaluation** — keyword coverage, quality scoring, response time
- **Search relevance evaluation** — Precision@K, MRR, type accuracy
- **Documentation quality metrics** — completeness, type coverage, search quality
- **Impact analysis accuracy** — risk validation, history integrity
- **Knowledge graph validation** — node/relationship counts, analytics queries
- **Architecture generation validation** — model listing, dependency graph
- **Load testing** — concurrent health checks, search, AI chat with latency percentiles
- **Performance regression detection** — automated alerting on degradation
- **Reports** — JSON, Markdown, HTML with dark-themed dashboards
- **Comparison reports** — cross-run trend analysis
- **CI/CD integration** — GitHub Actions workflow with artifact upload

## Quick Start

```bash
# Run benchmarks against local backend
python -m benchmarks run --sizes small

# Run specific categories
python -m benchmarks run --sizes small --categories pipeline search ai

# Run against custom URL
python -m benchmarks run --url http://staging:8000 --sizes small medium

# List past runs
python -m benchmarks list

# Generate comparison report
python -m benchmarks compare --last 5
```

## Repository Size Tiers

| Tier | Description | Expected Files |
|------|-------------|----------------|
| `small` | Small library (~50 files) | 50 |
| `medium` | Medium library (~150 files) | 150 |
| `large` | Large framework (~300 files) | 300 |
| `xlarge` | Extra-large framework (~5000 files) | 5000 |

## Benchmark Categories

| Category | Benchmarks |
|----------|-----------|
| `pipeline` | health_check, repo_connect, repo_scan, repo_parse |
| `graph` | graph_sync, graph_statistics, graph_connected_files, graph_languages |
| `search` | embedding_sync, search_relevance (25 queries), search_relevance_aggregate |
| `ai` | ai_quality (20 queries), ai_quality_aggregate |
| `documentation` | doc_generation, doc_quality, doc_search_quality |
| `architecture` | arch_generation, arch_models_list, arch_dependencies |
| `impact` | impact_analysis, impact_history, impact_risk |
| `load` | load_health_check, load_search, load_ai_chat |

## Reports

Reports are generated in `benchmarks/results/`:

- `report_<run_id>.json` — Machine-readable results
- `report_<run_id>.md` — Markdown summary
- `report_<run_id>.html` — Dark-themed HTML dashboard
- `comparison_report.md` — Multi-run trend comparison
- `regression_report.md` — Regression alerts (if detected)

## Regression Detection

Regressions are flagged when:
- **Warning**: Metric degrades by >15% vs baseline
- **Critical**: Metric degrades by >30% vs baseline

Applies to both performance metrics (response time) and quality metrics (keyword coverage, precision).

## CI/CD Integration

The framework includes a GitHub Actions workflow (`.github/workflows/benchmark.yml`):
- Runs weekly on Monday at 3am UTC
- Can be triggered manually with custom sizes/categories
- Uploads results as artifacts (90-day retention)
- Fails on critical regressions
- Posts summary to GitHub Step Summary

## Running Tests

```bash
cd benchmarks
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BENCHMARK_API_URL` | `http://localhost:8000` | Backend API URL |
| `BENCHMARK_OUTPUT_DIR` | `benchmarks/results` | Output directory |

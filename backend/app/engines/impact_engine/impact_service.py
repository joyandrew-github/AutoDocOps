"""ImpactAnalysisService — evaluates change impact across the entire codebase."""
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.impact_repo import ImpactRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.parser_repo import ParserRepository
from app.repositories.memory_repo import MemoryRepository
from app.models.parser import Function, Class, Method, Import
from app.core.logging import get_logger

logger = get_logger(__name__)

RISK_WEIGHTS = {
    "dependency": 0.25,
    "api": 0.20,
    "cross_module": 0.15,
    "circular_dep": 0.15,
    "change_frequency": 0.10,
    "architecture": 0.15,
}


def _risk_level(score: float) -> str:
    if score >= 0.75:
        return "critical"
    elif score >= 0.50:
        return "high"
    elif score >= 0.25:
        return "medium"
    return "low"


class ImpactAnalysisService:
    """Analyzes change impact using Memory Engine, Parser, and dependency data."""

    def __init__(self, db: Session):
        self.db = db
        self.impact_repo = ImpactRepository(db)
        self.repo_repo = RepositoryRepository(db)
        self.parser_repo = ParserRepository(db)
        self.memory_repo = MemoryRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_impact(self, repository_id: int, commit_hash: str | None = None) -> dict:
        """Run a full impact analysis for the latest changes."""
        start = time.time()
        stats = {
            "total_changes": 0,
            "total_affected": 0,
            "overall_risk_level": "low",
            "overall_risk_score": 0.0,
            "duration_seconds": 0.0,
            "errors": [],
        }

        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        snapshot = self.memory_repo.get_latest_snapshot(repository_id)
        analysis = self.impact_repo.create_analysis(
            repository_id=repository_id,
            trigger_type="manual",
            commit_hash=commit_hash,
            snapshot_id=snapshot.id if snapshot else None,
        )
        self.impact_repo.update_analysis(analysis, status="running", started_at=datetime.now(timezone.utc))

        try:
            # Collect changes from Memory Engine
            file_changes, entity_changes = self._collect_changes(repository_id)
            stats["total_changes"] = len(file_changes) + len(entity_changes)

            # Build dependency index
            dep_index = self._build_dependency_index(repository_id)

            # Analyse each changed entity
            results = []
            for ec in entity_changes:
                try:
                    result_data = self._analyze_entity_impact(
                        repository_id, analysis.id, ec, dep_index,
                    )
                    results.append(result_data)
                except Exception as e:
                    stats["errors"].append(f"entity {ec.get('entity_name', '?')}: {e}")

            for fc in file_changes:
                try:
                    result_data = self._analyze_file_impact(
                        repository_id, analysis.id, fc, dep_index,
                    )
                    results.append(result_data)
                except Exception as e:
                    stats["errors"].append(f"file {fc.get('file_path', '?')}: {e}")

            # Store results
            if results:
                stored = self.impact_repo.bulk_create_results(results)
                stats["total_affected"] = len(stored)

            # Risk assessment
            risk = self._compute_risk_assessment(
                repository_id, analysis.id, results, dep_index, file_changes, entity_changes,
            )
            stats["overall_risk_level"] = risk["risk_level"]
            stats["overall_risk_score"] = risk["risk_score"]

            # Test recommendations
            test_recs = self._generate_test_recommendations(results)

            self.impact_repo.create_risk_assessment(
                analysis_id=analysis.id,
                risk_level=risk["risk_level"],
                risk_score=risk["risk_score"],
                dependency_score=risk.get("dependency_score", 0.0),
                api_score=risk.get("api_score", 0.0),
                cross_module_score=risk.get("cross_module_score", 0.0),
                circular_dep_score=risk.get("circular_dep_score", 0.0),
                change_frequency_score=risk.get("change_frequency_score", 0.0),
                architecture_score=risk.get("architecture_score", 0.0),
                test_recommendations=json.dumps(test_recs),
                summary=risk.get("summary", ""),
                factors=risk.get("factors"),
            )

            duration = round(time.time() - start, 3)
            stats["duration_seconds"] = duration
            summary = (
                f"Impact analysis: {stats['total_changes']} changes, "
                f"{stats['total_affected']} affected entities, "
                f"risk={stats['overall_risk_level']} ({stats['overall_risk_score']:.2f})"
            )
            self.impact_repo.update_analysis(analysis,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_changes=stats["total_changes"],
                total_affected=stats["total_affected"],
                overall_risk_level=stats["overall_risk_level"],
                overall_risk_score=stats["overall_risk_score"],
                summary=summary,
                duration_seconds=duration,
            )
            logger.info(f"Impact analysis completed for repository {repository_id}: {summary}")

        except Exception as e:
            logger.error(f"Impact analysis failed for repository {repository_id}: {e}")
            self.impact_repo.update_analysis(analysis,
                status="failed", error_message=str(e), completed_at=datetime.now(timezone.utc),
            )
            stats["errors"].append(str(e))

        return stats

    def get_analysis(self, analysis_id: int):
        return self.impact_repo.get_analysis_by_id(analysis_id)

    def get_analysis_history(self, repository_id: int, limit: int = 20):
        return self.impact_repo.get_analyses_by_repository(repository_id, limit)

    def get_entity_impact(self, repository_id: int, entity_name: str):
        analysis = self.impact_repo.get_latest_analysis(repository_id)
        if not analysis:
            return None
        return self.impact_repo.get_result_by_entity_name(analysis.id, entity_name)

    def get_risk_assessment(self, repository_id: int):
        analysis = self.impact_repo.get_latest_analysis(repository_id)
        if not analysis:
            return None
        return self.impact_repo.get_risk_assessment(analysis.id)

    def export_analysis(self, analysis_id: int, format: str = "json") -> str | None:
        analysis = self.impact_repo.get_analysis_by_id(analysis_id)
        if not analysis:
            return None
        results = self.impact_repo.get_results_by_analysis(analysis_id)
        risk = self.impact_repo.get_risk_assessment(analysis_id)

        data = {
            "id": analysis.id,
            "repository_id": analysis.repository_id,
            "status": analysis.status,
            "total_changes": analysis.total_changes,
            "total_affected": analysis.total_affected,
            "overall_risk_level": analysis.overall_risk_level,
            "overall_risk_score": analysis.overall_risk_score,
            "summary": analysis.summary,
            "results": [
                {
                    "entity_type": r.entity_type,
                    "entity_name": r.entity_name,
                    "file_path": r.file_path,
                    "change_type": r.change_type,
                    "risk_level": r.risk_level,
                    "risk_score": r.risk_score,
                    "direct_dependents": r.direct_dependents,
                    "indirect_dependents": r.indirect_dependents,
                    "recommendations": r.recommendations,
                }
                for r in results
            ],
            "risk_assessment": {
                "risk_level": risk.risk_level,
                "risk_score": risk.risk_score,
                "test_recommendations": risk.test_recommendations,
                "summary": risk.summary,
            } if risk else None,
        }

        if format == "json":
            return json.dumps(data, indent=2, default=str)
        elif format == "markdown":
            return self._export_markdown(data)
        elif format == "html":
            return self._export_html(data)
        return json.dumps(data, indent=2, default=str)

    # ------------------------------------------------------------------
    # Private — change collection
    # ------------------------------------------------------------------

    def _collect_changes(self, repository_id: int) -> tuple[list[dict], list[dict]]:
        file_changes_out: list[dict] = []
        entity_changes_out: list[dict] = []

        change_sets = self.memory_repo.get_change_sets_by_repository(repository_id, limit=1)
        if not change_sets:
            return file_changes_out, entity_changes_out

        cs = change_sets[0]
        snapshot = self.memory_repo.get_latest_snapshot(repository_id)
        if not snapshot or cs.snapshot_id != snapshot.id:
            return file_changes_out, entity_changes_out

        fcs = self.memory_repo.get_file_changes_by_change_set(cs.id)
        for fc in fcs:
            file_changes_out.append({
                "file_path": fc.file_path,
                "change_type": fc.change_type,
            })

        ecs = self.memory_repo.get_entity_changes_by_change_set(cs.id)
        for ec in ecs:
            entity_changes_out.append({
                "entity_type": ec.entity_type,
                "entity_name": ec.entity_name,
                "file_path": ec.file_path,
                "change_type": ec.change_type,
            })

        return file_changes_out, entity_changes_out

    # ------------------------------------------------------------------
    # Private — dependency index
    # ------------------------------------------------------------------

    def _build_dependency_index(self, repository_id: int) -> dict:
        nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)
        files = self.repo_repo.get_files_by_repository(repository_id)
        file_map = {f.id: f for f in files}

        importers: dict[str, list[str]] = defaultdict(list)  # module -> [importing_files]
        file_entities: dict[str, list[str]] = defaultdict(list)  # file -> [entity_names]
        entity_file: dict[str, str] = {}  # entity_name -> file_path

        for n in nodes:
            rf = file_map.get(n.file_id)
            fp = rf.relative_path if rf else ""
            if isinstance(n, Import):
                module = getattr(n, "module", "") or ""
                if module:
                    importers[module].append(fp)
            if n.name:
                file_entities[fp].append(n.name)
                entity_file[n.name] = fp

        return {
            "importers": dict(importers),
            "file_entities": dict(file_entities),
            "entity_file": entity_file,
            "file_map": {f.relative_path: f for f in files},
        }

    # ------------------------------------------------------------------
    # Private — entity impact
    # ------------------------------------------------------------------

    def _analyze_entity_impact(self, repository_id: int, analysis_id: int, change: dict, dep_index: dict) -> dict:
        entity_name = change["entity_name"]
        entity_type = change["entity_type"]
        file_path = change.get("file_path", "")
        change_type = change["change_type"]

        direct = self._find_direct_dependents(entity_name, file_path, dep_index)
        indirect = self._find_indirect_dependents(direct, dep_index, depth=2)

        dep_count = len(direct) + len(indirect)
        is_api = self._is_api_entity(file_path, entity_name, dep_index)
        cross_module = self._count_cross_module(file_path, direct)

        score = min(1.0, dep_count * 0.05 + (0.3 if is_api else 0) + cross_module * 0.1)
        level = _risk_level(score)

        recs = []
        if is_api:
            recs.append("API change — verify backward compatibility")
        if dep_count > 5:
            recs.append(f"High fan-out: {dep_count} dependents — run regression tests")
        if cross_module > 0:
            recs.append(f"Cross-module impact ({cross_module} modules) — integration tests recommended")

        return {
            "analysis_id": analysis_id,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "file_path": file_path,
            "change_type": change_type,
            "impact_type": "direct",
            "risk_level": level,
            "risk_score": round(score, 3),
            "direct_dependents": len(direct),
            "indirect_dependents": len(indirect),
            "recommendations": "; ".join(recs) if recs else None,
            "details": {
                "direct_dependents": direct[:20],
                "indirect_dependents": indirect[:20],
                "is_api": is_api,
                "cross_module_count": cross_module,
            },
        }

    def _analyze_file_impact(self, repository_id: int, analysis_id: int, change: dict, dep_index: dict) -> dict:
        file_path = change["file_path"]
        change_type = change["change_type"]
        entities = dep_index.get("file_entities", {}).get(file_path, [])

        total_direct = 0
        total_indirect = 0
        for ename in entities:
            d = self._find_direct_dependents(ename, file_path, dep_index)
            total_direct += len(d)
            total_indirect += len(self._find_indirect_dependents(d, dep_index, depth=1))

        score = min(1.0, len(entities) * 0.03 + total_direct * 0.02)
        level = _risk_level(score)

        return {
            "analysis_id": analysis_id,
            "entity_type": "file",
            "entity_name": file_path,
            "file_path": file_path,
            "change_type": change_type,
            "impact_type": "direct",
            "risk_level": level,
            "risk_score": round(score, 3),
            "direct_dependents": total_direct,
            "indirect_dependents": total_indirect,
            "recommendations": f"File change affects {len(entities)} entities" if entities else None,
            "details": {"entities_in_file": entities[:30]},
        }

    # ------------------------------------------------------------------
    # Private — dependency traversal
    # ------------------------------------------------------------------

    def _find_direct_dependents(self, entity_name: str, file_path: str, dep_index: dict) -> list[str]:
        dependents: set[str] = set()
        importers = dep_index.get("importers", {})
        for module, importing_files in importers.items():
            if entity_name in module or file_path.replace("/", ".").replace(".py", "") in module:
                for f in importing_files:
                    if f != file_path:
                        dependents.add(f)
        return sorted(dependents)

    def _find_indirect_dependents(self, direct: list[str], dep_index: dict, depth: int = 2) -> list[str]:
        indirect: set[str] = set()
        current = set(direct)
        for _ in range(depth):
            next_level: set[str] = set()
            for fp in current:
                entities = dep_index.get("file_entities", {}).get(fp, [])
                for ename in entities:
                    deps = self._find_direct_dependents(ename, fp, dep_index)
                    for d in deps:
                        if d not in current and d not in indirect:
                            next_level.add(d)
            indirect.update(next_level)
            current = next_level
            if not current:
                break
        return sorted(indirect)

    @staticmethod
    def _is_api_entity(file_path: str, entity_name: str, dep_index: dict) -> bool:
        path_lower = file_path.lower()
        return any(kw in path_lower for kw in ["api", "endpoint", "route", "controller", "handler"])

    @staticmethod
    def _count_cross_module(file_path: str, dependents: list[str]) -> int:
        src_parts = file_path.rsplit("/", 1)
        src_module = src_parts[0] if len(src_parts) > 1 else "."
        modules: set[str] = set()
        for d in dependents:
            parts = d.rsplit("/", 1)
            m = parts[0] if len(parts) > 1 else "."
            if m != src_module:
                modules.add(m)
        return len(modules)

    # ------------------------------------------------------------------
    # Private — risk assessment
    # ------------------------------------------------------------------

    def _compute_risk_assessment(self, repository_id: int, analysis_id: int, results: list[dict], dep_index: dict, file_changes: list, entity_changes: list) -> dict:
        total_deps = sum(r.get("direct_dependents", 0) + r.get("indirect_dependents", 0) for r in results)
        api_count = sum(1 for r in results if r.get("details", {}).get("is_api"))
        cross_mod = sum(r.get("details", {}).get("cross_module_count", 0) for r in results)
        n_changes = len(file_changes) + len(entity_changes)

        dep_score = min(1.0, total_deps * 0.02)
        api_s = min(1.0, api_count * 0.25)
        cross_s = min(1.0, cross_mod * 0.1)
        circ_s = 0.0
        freq_s = min(1.0, n_changes * 0.05)
        arch_s = min(1.0, len(results) * 0.03)

        overall = (
            dep_score * RISK_WEIGHTS["dependency"]
            + api_s * RISK_WEIGHTS["api"]
            + cross_s * RISK_WEIGHTS["cross_module"]
            + circ_s * RISK_WEIGHTS["circular_dep"]
            + freq_s * RISK_WEIGHTS["change_frequency"]
            + arch_s * RISK_WEIGHTS["architecture"]
        )
        overall = round(min(1.0, overall), 3)
        level = _risk_level(overall)

        summary = (
            f"Risk {level} ({overall:.2f}): "
            f"{n_changes} changes, {total_deps} total dependents, "
            f"{api_count} API changes, {cross_mod} cross-module impacts"
        )

        return {
            "risk_level": level,
            "risk_score": overall,
            "dependency_score": round(dep_score, 3),
            "api_score": round(api_s, 3),
            "cross_module_score": round(cross_s, 3),
            "circular_dep_score": round(circ_s, 3),
            "change_frequency_score": round(freq_s, 3),
            "architecture_score": round(arch_s, 3),
            "summary": summary,
            "factors": {
                "total_dependents": total_deps,
                "api_changes": api_count,
                "cross_module_impacts": cross_mod,
                "change_count": n_changes,
            },
        }

    # ------------------------------------------------------------------
    # Private — test recommendations
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_test_recommendations(results: list[dict]) -> dict:
        unit_tests: list[str] = []
        integration_tests: list[str] = []
        regression_tests: list[str] = []

        for r in results:
            name = r.get("entity_name", "")
            etype = r.get("entity_type", "")
            risk = r.get("risk_level", "low")
            deps = r.get("direct_dependents", 0)

            if etype in ("function", "method", "class"):
                unit_tests.append(f"Test {etype} `{name}`")
            if deps > 0:
                integration_tests.append(f"Integration test for `{name}` ({deps} dependents)")
            if risk in ("high", "critical"):
                regression_tests.append(f"Regression test for `{name}` (risk={risk})")

        return {
            "unit_tests": unit_tests[:20],
            "integration_tests": integration_tests[:20],
            "regression_tests": regression_tests[:20],
        }

    # ------------------------------------------------------------------
    # Private — export
    # ------------------------------------------------------------------

    def _export_markdown(self, data: dict) -> str:
        parts = [f"# Impact Analysis Report\n"]
        parts.append(f"**Status:** {data.get('status', 'unknown')}\n")
        parts.append(f"**Changes:** {data.get('total_changes', 0)} | **Affected:** {data.get('total_affected', 0)}\n")
        parts.append(f"**Risk:** {data.get('overall_risk_level', 'low')} ({data.get('overall_risk_score', 0):.2f})\n")
        if data.get("summary"):
            parts.append(f"\n{data['summary']}\n")

        results = data.get("results", [])
        if results:
            parts.append("\n## Affected Entities\n")
            parts.append("| Entity | Type | Change | Risk | Dependents |\n|--------|------|--------|------|------------|\n")
            for r in results:
                parts.append(f"| `{r['entity_name'][:40]}` | {r['entity_type']} | {r['change_type']} | {r['risk_level']} | {r['direct_dependents']} |\n")

        risk = data.get("risk_assessment")
        if risk:
            parts.append(f"\n## Risk Assessment\n\n{risk.get('summary', '')}\n")

        return "".join(parts)

    def _export_html(self, data: dict) -> str:
        md = self._export_markdown(data)
        lines = md.split("\n")
        html = ["<!DOCTYPE html><html><head><meta charset='utf-8'><style>body{font-family:sans-serif;max-width:900px;margin:0 auto;padding:20px}table{border-collapse:collapse;width:100%}th,td{border:1px solid #ddd;padding:8px;text-align:left}th{background:#f4f4f4}code{background:#f0f0f0;padding:2px 4px;border-radius:3px}</style></head><body>"]
        in_table = False
        for line in lines:
            if line.startswith("# "):
                html.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("| ") and not in_table:
                in_table = True
                html.append("<table>")
                cells = [c.strip() for c in line.split("|")[1:-1]]
                html.append("<tr>" + "".join(f"<th>{c}</th>" for c in cells) + "</tr>")
            elif line.startswith("|---"):
                continue
            elif line.startswith("| ") and in_table:
                cells = [c.strip() for c in line.split("|")[1:-1]]
                html.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
            elif in_table and not line.startswith("|"):
                html.append("</table>")
                in_table = False
                if line.strip():
                    html.append(f"<p>{line}</p>")
            elif line.strip():
                html.append(f"<p>{line}</p>")
        if in_table:
            html.append("</table>")
        html.append("</body></html>")
        return "\n".join(html)

"""Pull request analysis service."""
from __future__ import annotations
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.github_repo import GitHubRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


def run_pr_analysis(db: Session, job) -> dict:
    """Analyse a pull request by inspecting changed files against existing engines."""
    gh = GitHubRepository(db)
    meta = job.metadata_ or {}
    connected_repo_id = job.connected_repository_id
    cr = gh.get_connected_repo(connected_repo_id) if connected_repo_id else None
    repository_id = cr.repository_id if cr else meta.get("repository_id")
    pr_number = meta.get("pr_number", 0)
    pr_title = meta.get("pr_title", "")
    pr_author = meta.get("pr_author", "")
    head_branch = meta.get("head_branch", "")
    base_branch = meta.get("base_branch", "")
    head_sha = meta.get("head_sha", "")
    changed_files_list = meta.get("changed_files", [])

    start = time.time()

    # Count entity changes by querying parser
    changed_classes = 0
    changed_functions = 0
    if repository_id:
        try:
            from app.repositories.parser_repo import ParserRepository
            pr_repo = ParserRepository(db)
            all_classes = pr_repo.get_classes_by_repository(repository_id)
            all_fns = pr_repo.get_functions_by_repository(repository_id)
            changed_files_set = set(changed_files_list)
            changed_classes = sum(1 for c in all_classes if getattr(c, "file_path", "") in changed_files_set)
            changed_functions = sum(1 for f in all_fns if getattr(f, "file_path", "") in changed_files_set)
        except Exception:
            pass

    # Risk scoring
    risk_score = min(1.0,
                     len(changed_files_list) * 0.02
                     + changed_classes * 0.05
                     + changed_functions * 0.03)
    if risk_score >= 0.75:
        risk_level = "critical"
    elif risk_score >= 0.50:
        risk_level = "high"
    elif risk_score >= 0.25:
        risk_level = "medium"
    else:
        risk_level = "low"

    # Breaking changes heuristic
    breaking: list[str] = []
    for fp in changed_files_list:
        fp_lower = fp.lower()
        if any(kw in fp_lower for kw in ["api", "endpoint", "route", "proto", "schema"]):
            breaking.append(f"API file changed: {fp}")

    # Recommended tests
    recommended_tests = {
        "unit_tests": [f"Test file {fp}" for fp in changed_files_list[:10] if fp.endswith(".py")],
        "integration_tests": [f"Integration for {fp}" for fp in changed_files_list[:5] if "api" in fp.lower() or "service" in fp.lower()],
        "regression_tests": [f"Regression for PR#{pr_number}"] if risk_level in ("high", "critical") else [],
    }

    # Architecture / documentation impact
    arch_impact = "High" if any("model" in fp.lower() or "schema" in fp.lower() for fp in changed_files_list) else "Low"
    doc_impact = "High" if any("readme" in fp.lower() or "doc" in fp.lower() for fp in changed_files_list) else "Low"

    summary = (
        f"PR #{pr_number}: {len(changed_files_list)} files changed, "
        f"{changed_classes} classes, {changed_functions} functions. "
        f"Risk: {risk_level} ({risk_score:.2f}). "
        f"Breaking changes: {len(breaking)}."
    )

    # Store analysis
    pra = gh.create_pr_analysis(
        connected_repository_id=connected_repo_id,
        pr_number=pr_number,
        pr_title=pr_title,
        pr_author=pr_author,
        head_branch=head_branch,
        base_branch=base_branch,
        head_sha=head_sha,
        status="completed",
        changed_files=len(changed_files_list),
        changed_classes=changed_classes,
        changed_functions=changed_functions,
        architecture_impact=arch_impact,
        documentation_impact=doc_impact,
        risk_score=round(risk_score, 3),
        risk_level=risk_level,
        breaking_changes=breaking,
        recommended_tests=recommended_tests,
        summary=summary,
        details={"changed_files": changed_files_list},
        completed_at=datetime.now(timezone.utc),
    )

    duration = round(time.time() - start, 3)
    logger.info(f"PR analysis #{pr_number}: {summary}")
    return {
        "pr_analysis_id": pra.id,
        "pr_number": pr_number,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "duration": duration,
    }

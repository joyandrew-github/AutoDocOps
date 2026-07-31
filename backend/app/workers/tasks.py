from app.core.celery_app import celery_app
from app.core.logging import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def run_push_pipeline(self, repo_id: int, commit_sha: str, branch: str, changed_files: list[str]) -> dict:
    """Celery task for push pipeline processing."""
    logger.info(f"[Celery] Push pipeline started: repo={repo_id} sha={commit_sha}")
    try:
        from app.db.session import SessionLocal
        from app.engines.github_engine.pipeline import AutoPipeline
        db = SessionLocal()
        try:
            pipeline = AutoPipeline(db)
            result = pipeline.run(repo_id, commit_sha, branch, changed_files)
            logger.info(f"[Celery] Push pipeline completed: repo={repo_id}")
            return result
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"[Celery] Push pipeline failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_pr_analysis(self, repo_id: int, pr_number: int, changed_files: list[str]) -> dict:
    """Celery task for pull request analysis."""
    logger.info(f"[Celery] PR analysis started: repo={repo_id} pr=#{pr_number}")
    try:
        from app.db.session import SessionLocal
        from app.engines.github_engine.pr_analysis import PRAnalyzer
        db = SessionLocal()
        try:
            analyzer = PRAnalyzer(db)
            result = analyzer.analyze(repo_id, pr_number, changed_files)
            logger.info(f"[Celery] PR analysis completed: repo={repo_id} pr=#{pr_number}")
            return result
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"[Celery] PR analysis failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task
def health_check_task() -> dict:
    """Simple task for verifying Celery connectivity."""
    return {"status": "ok", "worker": "autodocops"}

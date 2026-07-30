"""Background job queue with retry logic and failure tracking."""
from __future__ import annotations
import time
import threading
from datetime import datetime, timezone
from typing import Callable, Any
from sqlalchemy.orm import Session
from app.repositories.github_repo import GitHubRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3


class JobQueue:
    """In-process async job queue with retry and failure tracking."""

    def __init__(self, db: Session):
        self.db = db
        self.gh_repo = GitHubRepository(db)
        self._handlers: dict[str, Callable] = {}

    def register_handler(self, job_type: str, handler: Callable) -> None:
        self._handlers[job_type] = handler

    @property
    def handlers(self) -> dict[str, Callable]:
        return dict(self._handlers)

    def enqueue(self, job_type: str, connected_repo_id: int | None = None,
                webhook_event_id: int | None = None, priority: int = 5,
                metadata: dict | None = None) -> int:
        job = self.gh_repo.create_job(
            job_type=job_type,
            connected_repository_id=connected_repo_id,
            webhook_event_id=webhook_event_id,
            priority=priority,
            metadata_=metadata,
        )
        logger.info(f"Enqueued job {job.id} type={job_type}")
        return job.id

    def process_job(self, job_id: int) -> dict[str, Any]:
        job = self.gh_repo.get_job(job_id)
        if not job:
            return {"status": "error", "error": "Job not found"}

        handler = self._handlers.get(job.job_type)
        if not handler:
            self.gh_repo.update_job(job, status="failed", error_message=f"No handler for {job.job_type}")
            return {"status": "error", "error": f"No handler for {job.job_type}"}

        self.gh_repo.update_job(job, status="running", started_at=datetime.now(timezone.utc),
                                attempt=job.attempt + 1)
        start = time.time()
        try:
            result = handler(self.db, job)
            duration = round(time.time() - start, 3)
            self.gh_repo.update_job(job, status="completed", completed_at=datetime.now(timezone.utc),
                                    duration_seconds=duration, result=result or {})
            logger.info(f"Job {job.id} completed in {duration}s")
            return {"status": "completed", "duration": duration, "result": result}
        except Exception as e:
            duration = round(time.time() - start, 3)
            logger.error(f"Job {job.id} failed (attempt {job.attempt}): {e}")
            if job.attempt < job.max_retries:
                self.gh_repo.update_job(job, status="queued", error_message=str(e),
                                        duration_seconds=duration)
                return {"status": "retry", "attempt": job.attempt, "error": str(e)}
            else:
                self.gh_repo.update_job(job, status="failed", error_message=str(e),
                                        completed_at=datetime.now(timezone.utc),
                                        duration_seconds=duration)
                return {"status": "failed", "error": str(e)}

    def process_job_async(self, job_id: int) -> None:
        t = threading.Thread(target=self.process_job, args=(job_id,), daemon=True)
        t.start()

    def retry_failed_jobs(self, connected_repo_id: int | None = None) -> int:
        jobs = self.gh_repo.get_queued_jobs(limit=20)
        retried = 0
        for job in jobs:
            if connected_repo_id and job.connected_repository_id != connected_repo_id:
                continue
            if job.attempt < job.max_retries:
                self.process_job(job.id)
                retried += 1
        return retried

    def get_job_status(self, job_id: int) -> dict | None:
        job = self.gh_repo.get_job(job_id)
        if not job:
            return None
        return {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "attempt": job.attempt,
            "max_retries": job.max_retries,
            "duration_seconds": job.duration_seconds,
            "error_message": job.error_message,
            "result": job.result,
        }

"""Webhook handler — receives, validates, and dispatches GitHub webhook events."""
from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.github_repo import GitHubRepository
from app.engines.github_engine.security import verify_webhook_signature
from app.engines.github_engine.job_queue import JobQueue
from app.engines.github_engine.pipeline import run_push_pipeline
from app.engines.github_engine.pr_analysis import run_pr_analysis
from app.core.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_EVENTS = {
    "push", "pull_request", "create", "delete", "release",
    "repository", "installation", "installation_repositories", "ping",
}


class WebhookHandler:
    """Processes incoming GitHub webhook events."""

    def __init__(self, db: Session):
        self.db = db
        self.gh_repo = GitHubRepository(db)
        self.job_queue = JobQueue(db)
        self._register_handlers()

    def _register_handlers(self) -> None:
        self.job_queue.register_handler("push_pipeline", run_push_pipeline)
        self.job_queue.register_handler("pr_analysis", run_pr_analysis)

    def handle_webhook(self, event_type: str, delivery_id: str, payload: dict,
                       signature: str | None = None, raw_body: bytes | None = None) -> dict:
        repo_name = payload.get("repository", {}).get("full_name", "")
        sender = payload.get("sender", {}).get("login", "")
        ref = payload.get("ref", "")
        action = payload.get("action", "")

        # Validate signature if secret exists for the repo
        sig_valid = False
        cr = self.gh_repo.get_connected_repo_by_full_name(repo_name)
        if cr and cr.webhook_secret and signature and raw_body:
            sig_valid = verify_webhook_signature(raw_body, signature, cr.webhook_secret)
        elif not signature:
            sig_valid = True  # no signature provided, consider valid for repos without secret

        # Store event
        ev = self.gh_repo.create_webhook_event(
            event_type=event_type,
            action=action,
            delivery_id=delivery_id,
            repository_full_name=repo_name,
            sender=sender,
            ref=ref,
            payload=payload,
            signature_valid=sig_valid,
        )

        if event_type not in SUPPORTED_EVENTS:
            self.gh_repo.update_webhook_event(ev, status="ignored",
                                              processed_at=datetime.now(timezone.utc))
            return {"status": "ignored", "reason": f"Unsupported event: {event_type}"}

        if event_type == "ping":
            self.gh_repo.update_webhook_event(ev, status="processed",
                                              processed_at=datetime.now(timezone.utc))
            return {"status": "pong"}

        if not cr:
            self.gh_repo.update_webhook_event(ev, status="skipped",
                                              error_message="Repository not connected",
                                              processed_at=datetime.now(timezone.utc))
            return {"status": "skipped", "reason": "Repository not connected"}

        # Dispatch event to appropriate handler
        result = self._dispatch(event_type, ev, cr, payload)
        self.gh_repo.update_webhook_event(ev, status="processed",
                                          processed_at=datetime.now(timezone.utc))
        return result

    def _dispatch(self, event_type: str, ev, cr, payload: dict) -> dict:
        if event_type == "push":
            return self._handle_push(ev, cr, payload)
        elif event_type == "pull_request":
            return self._handle_pull_request(ev, cr, payload)
        elif event_type in ("create", "delete"):
            return self._handle_branch_event(ev, cr, payload, event_type)
        elif event_type == "release":
            return self._handle_release(ev, cr, payload)
        elif event_type in ("installation", "installation_repositories"):
            return self._handle_installation(ev, payload)
        elif event_type == "repository":
            return self._handle_repository_event(ev, payload)
        return {"status": "processed", "event": event_type}

    def _handle_push(self, ev, cr, payload: dict) -> dict:
        commits = payload.get("commits", [])
        changed_files = set()
        for c in commits:
            changed_files.update(c.get("added", []))
            changed_files.update(c.get("modified", []))
            changed_files.update(c.get("removed", []))

        job_id = self.job_queue.enqueue(
            "push_pipeline",
            connected_repo_id=cr.id,
            webhook_event_id=ev.id,
            metadata={
                "repository_id": cr.repository_id,
                "ref": payload.get("ref", ""),
                "commit_hash": payload.get("after", ""),
                "changed_files": sorted(changed_files),
            },
        )
        self.job_queue.process_job_async(job_id)
        logger.info(f"Push webhook for {cr.full_name}: {len(changed_files)} files, job={job_id}")
        return {"status": "queued", "job_id": job_id, "files_changed": len(changed_files)}

    def _handle_pull_request(self, ev, cr, payload: dict) -> dict:
        pr = payload.get("pull_request", {})
        action = payload.get("action", "")
        if action not in ("opened", "synchronize", "reopened"):
            return {"status": "processed", "action": action}

        changed_files = []
        if pr.get("changed_files"):
            changed_files = [f"file_{i}" for i in range(min(pr["changed_files"], 50))]

        job_id = self.job_queue.enqueue(
            "pr_analysis",
            connected_repo_id=cr.id,
            webhook_event_id=ev.id,
            metadata={
                "repository_id": cr.repository_id,
                "pr_number": pr.get("number", 0),
                "pr_title": pr.get("title", ""),
                "pr_author": pr.get("user", {}).get("login", ""),
                "head_branch": pr.get("head", {}).get("ref", ""),
                "base_branch": pr.get("base", {}).get("ref", ""),
                "head_sha": pr.get("head", {}).get("sha", ""),
                "changed_files": changed_files,
            },
        )
        self.job_queue.process_job_async(job_id)
        logger.info(f"PR webhook for {cr.full_name} PR#{pr.get('number')}: job={job_id}")
        return {"status": "queued", "job_id": job_id, "pr_number": pr.get("number")}

    def _handle_branch_event(self, ev, cr, payload: dict, event_type: str) -> dict:
        ref_type = payload.get("ref_type", "")
        ref_name = payload.get("ref", "")
        logger.info(f"Branch event {event_type}: {ref_type} {ref_name} on {cr.full_name}")
        return {"status": "processed", "event": event_type, "ref_type": ref_type}

    def _handle_release(self, ev, cr, payload: dict) -> dict:
        release = payload.get("release", {})
        tag = release.get("tag_name", "")
        logger.info(f"Release event: {tag} on {cr.full_name}")
        return {"status": "processed", "tag": tag}

    def _handle_installation(self, ev, payload: dict) -> dict:
        action = payload.get("action", "")
        installation_id = payload.get("installation", {}).get("id", 0)
        logger.info(f"Installation event: {action}, id={installation_id}")
        return {"status": "processed", "action": action, "installation_id": installation_id}

    def _handle_repository_event(self, ev, payload: dict) -> dict:
        action = payload.get("action", "")
        logger.info(f"Repository event: {action}")
        return {"status": "processed", "action": action}

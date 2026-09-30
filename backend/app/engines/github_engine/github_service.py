"""GitHub service — repository management, connect/disconnect, sync."""
from __future__ import annotations
import time
import secrets
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.github_repo import GitHubRepository
from app.engines.github_engine.security import encrypt_token
from app.engines.github_engine.job_queue import JobQueue
from app.engines.github_engine.pipeline import run_push_pipeline
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitHubService:
    """High-level GitHub integration service."""

    def __init__(self, db: Session):
        self.db = db
        self.gh_repo = GitHubRepository(db)
        self.job_queue = JobQueue(db)
        self.job_queue.register_handler("push_pipeline", run_push_pipeline)

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    def register_account(self, user_id: int, github_user_id: int,
                         github_username: str, access_token: str,
                         auth_type: str = "pat", **kwargs) -> dict:
        existing = self.gh_repo.get_account_by_user(user_id)
        if existing:
            self.gh_repo.update_account(
                existing,
                github_user_id=github_user_id,
                github_username=github_username,
                access_token_encrypted=encrypt_token(access_token),
                auth_type=auth_type,
                **kwargs,
            )
            return {"id": existing.id, "status": "updated"}

        acct = self.gh_repo.create_account(
            user_id=user_id,
            github_user_id=github_user_id,
            github_username=github_username,
            access_token_encrypted=encrypt_token(access_token),
            auth_type=auth_type,
            **kwargs,
        )
        return {"id": acct.id, "status": "created"}

    # ------------------------------------------------------------------
    # Repository connect / disconnect
    # ------------------------------------------------------------------

    def connect_repository(self, github_account_id: int, github_repo_id: int,
                           full_name: str, repository_id: int | None = None,
                           default_branch: str = "main",
                           is_private: bool = False) -> dict:
        # Sanitize full_name if user provided full URL (e.g., https://github.com/user/repo)
        cleaned_name = full_name.strip()
        if "github.com/" in cleaned_name:
            cleaned_name = cleaned_name.split("github.com/")[-1].strip("/")
        if cleaned_name.endswith(".git"):
            cleaned_name = cleaned_name[:-4]

        # Ensure a valid GitHubAccount exists in DB
        from app.models.github import GitHubAccount, ConnectedRepository
        account = self.db.query(GitHubAccount).filter(GitHubAccount.id == github_account_id).first()
        if not account:
            account = self.db.query(GitHubAccount).filter(GitHubAccount.is_active.is_(True)).first()
            if not account:
                from app.models.user import User
                user = self.db.query(User).first()
                if not user:
                    user = User(
                        email="admin@autodocops.local",
                        username="admin",
                        hashed_password="!",
                        is_active=True,
                    )
                    self.db.add(user)
                    self.db.commit()
                    self.db.refresh(user)
                account = GitHubAccount(
                    user_id=user.id,
                    github_user_id=user.id,
                    github_username=user.username or "default",
                    auth_type="pat",
                    is_active=True,
                )
                self.db.add(account)
                self.db.commit()
                self.db.refresh(account)
            github_account_id = account.id

        existing = self.gh_repo.get_connected_repo_by_full_name(cleaned_name)
        if existing and existing.is_active:
            return {"id": existing.id, "status": "already_connected"}

        webhook_secret = secrets.token_hex(20)
        cr = self.gh_repo.connect_repository(
            github_account_id=github_account_id,
            github_repo_id=github_repo_id or (existing.github_repo_id if existing else 1),
            full_name=cleaned_name,
            repository_id=repository_id,
            default_branch=default_branch,
            is_private=is_private,
            webhook_secret=webhook_secret,
        )
        logger.info(f"Connected repository {cleaned_name} (id={cr.id})")

        # Automatically clone and ingest core repository
        try:
            from app.services.repository_service import RepositoryService
            from app.engines.parser_engine.parser_service import ParserService
            from app.engines.architecture_engine.architecture_service import ArchitectureService
            from app.engines.documentation_engine.documentation_service import DocumentationService

            repo_svc = RepositoryService(self.db)
            core_repo = repo_svc.connect_repository(f"https://github.com/{cleaned_name}.git")
            cr.repository_id = core_repo.id
            self.db.commit()
            self.db.refresh(cr)

            repo_svc.scan_repository(core_repo.id)
            ParserService(self.db).parse_repository(core_repo.id)
            ArchitectureService(self.db).generate_architecture(core_repo.id)
            DocumentationService(self.db).generate_documentation(core_repo.id)
            from app.db.neo4j import get_neo4j_client
            from app.engines.graph_engine.graph_sync_service import GraphSyncService
            GraphSyncService(self.db, get_neo4j_client()).sync_repository(core_repo.id)
            logger.info(f"Auto-ingested, generated architecture, docs, and knowledge graph for {cleaned_name} (repo_id={core_repo.id})")
        except Exception as e:
            logger.error(f"Auto-ingestion error for {cleaned_name}: {e}")

        return {"id": cr.id, "status": "connected", "webhook_secret": webhook_secret}

    def disconnect_repository(self, repo_id: int) -> dict:
        ok = self.gh_repo.disconnect_repository(repo_id)
        if ok:
            logger.info(f"Disconnected repository id={repo_id}")
            return {"status": "disconnected"}
        return {"status": "not_found"}

    def get_connected_repositories(self, account_id: int) -> list[dict]:
        from app.models.github import ConnectedRepository
        from sqlalchemy import desc
        repos = self.gh_repo.get_connected_repos_by_account(account_id)
        if not repos:
            repos = (
                self.db.query(ConnectedRepository)
                .filter(ConnectedRepository.is_active.is_(True))
                .order_by(desc(ConnectedRepository.created_at))
                .all()
            )
        return [
            {
                "id": r.id,
                "full_name": r.full_name,
                "default_branch": r.default_branch,
                "selected_branch": r.selected_branch,
                "is_private": r.is_private,
                "auto_sync": r.auto_sync,
                "sync_status": r.sync_status,
                "last_synced_at": str(r.last_synced_at) if r.last_synced_at else None,
            }
            for r in repos
        ]

    def sync_repository(self, connected_repo_id: int) -> dict:
        from app.models.github import ConnectedRepository
        from app.models.repository import Repository
        from app.services.repository_service import RepositoryService
        from app.engines.parser_engine.parser_service import ParserService
        from app.engines.architecture_engine.architecture_service import ArchitectureService
        from app.engines.documentation_engine.documentation_service import DocumentationService

        cr = self.gh_repo.get_connected_repo(connected_repo_id)
        if not cr:
            cr = self.db.query(ConnectedRepository).filter(
                (ConnectedRepository.repository_id == connected_repo_id) |
                (ConnectedRepository.id == connected_repo_id)
            ).first()
            if not cr:
                cr = self.db.query(ConnectedRepository).filter(ConnectedRepository.is_active.is_(True)).first()
        if not cr:
            return {"status": "not_found"}

        if not cr.repository_id:
            repo_svc = RepositoryService(self.db)
            core_repo = repo_svc.connect_repository(f"https://github.com/{cr.full_name}.git")
            cr.repository_id = core_repo.id
            self.db.commit()
            self.db.refresh(cr)

        sync = self.gh_repo.create_sync(
            connected_repository_id=cr.id,
            sync_type="manual",
            branch=cr.selected_branch or cr.default_branch,
            status="running",
        )
        self.gh_repo.update_connected_repo(cr, sync_status="syncing")

        start = time.time()
        try:
            # Trigger real scan, parse, architecture, and docs generation
            if cr.repository_id:
                repo_svc = RepositoryService(self.db)
                repo_svc.scan_repository(cr.repository_id)
                ParserService(self.db).parse_repository(cr.repository_id)
                ArchitectureService(self.db).generate_architecture(cr.repository_id)
                DocumentationService(self.db).generate_documentation(cr.repository_id)
                from app.db.neo4j import get_neo4j_client
                from app.engines.graph_engine.graph_sync_service import GraphSyncService
                GraphSyncService(self.db, get_neo4j_client()).sync_repository(cr.repository_id)

            duration = round(time.time() - start, 3)
            self.gh_repo.update_sync(sync,
                status="completed",
                duration_seconds=duration,
                pipeline_steps={"scan": "ok", "parse": "ok", "graph": "ok", "architecture": "ok", "docs": "ok"},
                completed_at=datetime.now(timezone.utc),
            )
            self.gh_repo.update_connected_repo(cr, sync_status="synced",
                                               last_synced_at=datetime.now(timezone.utc))
            return {"status": "completed", "sync_id": sync.id, "duration": duration}
        except Exception as e:
            duration = round(time.time() - start, 3)
            self.gh_repo.update_sync(sync, status="failed", error_message=str(e),
                                     duration_seconds=duration,
                                     completed_at=datetime.now(timezone.utc))
            self.gh_repo.update_connected_repo(cr, sync_status="failed")
            logger.error(f"Sync failed for repo {cr.full_name}: {e}")
            return {"status": "failed", "error": str(e)}

    def select_branch(self, connected_repo_id: int, branch: str) -> dict:
        cr = self.gh_repo.get_connected_repo(connected_repo_id)
        if not cr:
            return {"status": "not_found"}
        self.gh_repo.update_connected_repo(cr, selected_branch=branch)
        return {"status": "updated", "selected_branch": branch}

    def detect_default_branch(self, connected_repo_id: int) -> dict:
        cr = self.gh_repo.get_connected_repo(connected_repo_id)
        if not cr:
            return {"status": "not_found"}
        return {"default_branch": cr.default_branch}

    # ------------------------------------------------------------------
    # Jobs & PR analysis
    # ------------------------------------------------------------------

    def get_jobs(self, connected_repo_id: int, limit: int = 20) -> list[dict]:
        jobs = self.gh_repo.get_jobs_by_repo(connected_repo_id, limit)
        return [
            {
                "id": j.id,
                "job_type": j.job_type,
                "status": j.status,
                "attempt": j.attempt,
                "duration_seconds": j.duration_seconds,
                "error_message": j.error_message,
                "created_at": str(j.created_at),
            }
            for j in jobs
        ]

    def get_job(self, job_id: int) -> dict | None:
        return self.job_queue.get_job_status(job_id)

    def get_pr_analysis(self, pr_id: int) -> dict | None:
        pra = self.gh_repo.get_pr_analysis(pr_id)
        if not pra:
            return None
        return {
            "id": pra.id,
            "pr_number": pra.pr_number,
            "pr_title": pra.pr_title,
            "pr_author": pra.pr_author,
            "head_branch": pra.head_branch,
            "base_branch": pra.base_branch,
            "status": pra.status,
            "changed_files": pra.changed_files,
            "changed_classes": pra.changed_classes,
            "changed_functions": pra.changed_functions,
            "architecture_impact": pra.architecture_impact,
            "documentation_impact": pra.documentation_impact,
            "risk_score": pra.risk_score,
            "risk_level": pra.risk_level,
            "breaking_changes": pra.breaking_changes,
            "recommended_tests": pra.recommended_tests,
            "summary": pra.summary,
        }

"""Data access layer for the GitHub Integration Engine."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.github import (
    GitHubAccount, ConnectedRepository, WebhookEvent,
    PipelineJob, PullRequestAnalysis, RepositorySync,
)


class GitHubRepository:
    """Data access for all GitHub integration entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- GitHubAccount ---

    def create_account(self, **kwargs) -> GitHubAccount:
        a = GitHubAccount(**kwargs)
        self.db.add(a)
        self.db.commit()
        self.db.refresh(a)
        return a

    def get_account_by_user(self, user_id: int) -> GitHubAccount | None:
        return self.db.query(GitHubAccount).filter(GitHubAccount.user_id == user_id, GitHubAccount.is_active.is_(True)).first()

    def get_account_by_github_username(self, username: str) -> GitHubAccount | None:
        return self.db.query(GitHubAccount).filter(GitHubAccount.github_username == username).first()

    def update_account(self, account: GitHubAccount, **kwargs) -> GitHubAccount:
        for k, v in kwargs.items():
            if hasattr(account, k):
                setattr(account, k, v)
        self.db.commit()
        self.db.refresh(account)
        return account

    # --- ConnectedRepository ---

    def connect_repository(self, **kwargs) -> ConnectedRepository:
        cr = ConnectedRepository(**kwargs)
        self.db.add(cr)
        self.db.commit()
        self.db.refresh(cr)
        return cr

    def disconnect_repository(self, repo_id: int) -> bool:
        cr = self.db.query(ConnectedRepository).filter(ConnectedRepository.id == repo_id).first()
        if not cr:
            return False
        cr.is_active = False
        self.db.commit()
        return True

    def get_connected_repo(self, repo_id: int) -> ConnectedRepository | None:
        return self.db.query(ConnectedRepository).filter(ConnectedRepository.id == repo_id).first()

    def get_connected_repos_by_account(self, account_id: int) -> list[ConnectedRepository]:
        return (
            self.db.query(ConnectedRepository)
            .filter(ConnectedRepository.github_account_id == account_id, ConnectedRepository.is_active.is_(True))
            .order_by(desc(ConnectedRepository.created_at))
            .all()
        )

    def get_connected_repo_by_full_name(self, full_name: str) -> ConnectedRepository | None:
        return (
            self.db.query(ConnectedRepository)
            .filter(ConnectedRepository.full_name == full_name, ConnectedRepository.is_active.is_(True))
            .first()
        )

    def update_connected_repo(self, cr: ConnectedRepository, **kwargs) -> ConnectedRepository:
        for k, v in kwargs.items():
            if hasattr(cr, k):
                setattr(cr, k, v)
        self.db.commit()
        self.db.refresh(cr)
        return cr

    # --- WebhookEvent ---

    def create_webhook_event(self, **kwargs) -> WebhookEvent:
        ev = WebhookEvent(**kwargs)
        self.db.add(ev)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    def get_webhook_event(self, event_id: int) -> WebhookEvent | None:
        return self.db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()

    def get_webhook_event_by_delivery(self, delivery_id: str) -> WebhookEvent | None:
        return self.db.query(WebhookEvent).filter(WebhookEvent.delivery_id == delivery_id).first()

    def update_webhook_event(self, ev: WebhookEvent, **kwargs) -> WebhookEvent:
        for k, v in kwargs.items():
            if hasattr(ev, k):
                setattr(ev, k, v)
        self.db.commit()
        self.db.refresh(ev)
        return ev

    # --- PipelineJob ---

    def create_job(self, **kwargs) -> PipelineJob:
        j = PipelineJob(**kwargs)
        self.db.add(j)
        self.db.commit()
        self.db.refresh(j)
        return j

    def get_job(self, job_id: int) -> PipelineJob | None:
        return self.db.query(PipelineJob).filter(PipelineJob.id == job_id).first()

    def get_jobs_by_repo(self, connected_repo_id: int, limit: int = 20) -> list[PipelineJob]:
        return (
            self.db.query(PipelineJob)
            .filter(PipelineJob.connected_repository_id == connected_repo_id)
            .order_by(desc(PipelineJob.created_at))
            .limit(limit)
            .all()
        )

    def get_queued_jobs(self, limit: int = 10) -> list[PipelineJob]:
        return (
            self.db.query(PipelineJob)
            .filter(PipelineJob.status == "queued")
            .order_by(PipelineJob.priority, PipelineJob.created_at)
            .limit(limit)
            .all()
        )

    def update_job(self, job: PipelineJob, **kwargs) -> PipelineJob:
        for k, v in kwargs.items():
            if hasattr(job, k):
                setattr(job, k, v)
        self.db.commit()
        self.db.refresh(job)
        return job

    # --- PullRequestAnalysis ---

    def create_pr_analysis(self, **kwargs) -> PullRequestAnalysis:
        pr = PullRequestAnalysis(**kwargs)
        self.db.add(pr)
        self.db.commit()
        self.db.refresh(pr)
        return pr

    def get_pr_analysis(self, pr_id: int) -> PullRequestAnalysis | None:
        return self.db.query(PullRequestAnalysis).filter(PullRequestAnalysis.id == pr_id).first()

    def get_pr_analysis_by_number(self, connected_repo_id: int, pr_number: int) -> PullRequestAnalysis | None:
        return (
            self.db.query(PullRequestAnalysis)
            .filter(PullRequestAnalysis.connected_repository_id == connected_repo_id, PullRequestAnalysis.pr_number == pr_number)
            .order_by(desc(PullRequestAnalysis.created_at))
            .first()
        )

    def update_pr_analysis(self, pr: PullRequestAnalysis, **kwargs) -> PullRequestAnalysis:
        for k, v in kwargs.items():
            if hasattr(pr, k):
                setattr(pr, k, v)
        self.db.commit()
        self.db.refresh(pr)
        return pr

    # --- RepositorySync ---

    def create_sync(self, **kwargs) -> RepositorySync:
        s = RepositorySync(**kwargs)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def get_sync(self, sync_id: int) -> RepositorySync | None:
        return self.db.query(RepositorySync).filter(RepositorySync.id == sync_id).first()

    def get_syncs_by_repo(self, connected_repo_id: int, limit: int = 10) -> list[RepositorySync]:
        return (
            self.db.query(RepositorySync)
            .filter(RepositorySync.connected_repository_id == connected_repo_id)
            .order_by(desc(RepositorySync.created_at))
            .limit(limit)
            .all()
        )

    def update_sync(self, s: RepositorySync, **kwargs) -> RepositorySync:
        for k, v in kwargs.items():
            if hasattr(s, k):
                setattr(s, k, v)
        self.db.commit()
        self.db.refresh(s)
        return s

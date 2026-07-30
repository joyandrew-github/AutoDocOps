from datetime import datetime, timezone
from pathlib import Path
from git import Repo, InvalidGitRepositoryError
from sqlalchemy.orm import Session
from app.repositories.memory_repo import MemoryRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class CommitTracker:
    """Tracks Git commit history and stores it in the database."""

    def __init__(self, db: Session):
        self.db = db
        self.memory_repo = MemoryRepository(db)

    def sync_commits(self, repository_id: int, local_path: str, branch: str | None = None, limit: int = 500) -> int:
        """Sync Git commits from a local repository into the database.

        Returns the number of new commits added.
        """
        repo_path = Path(local_path)
        if not repo_path.exists() or not (repo_path / ".git").exists():
            logger.warning(f"Not a valid Git repository: {local_path}")
            return 0

        try:
            repo = Repo(str(repo_path))
        except InvalidGitRepositoryError:
            logger.warning(f"Invalid Git repository: {local_path}")
            return 0

        # Determine branch
        if not branch:
            try:
                branch = repo.active_branch.name
            except TypeError:
                branch = "HEAD"

        logger.info(f"Syncing commits for repository {repository_id} from branch '{branch}'")

        new_commits = 0
        try:
            for commit in repo.iter_commits(branch, max_count=limit):
                # Check if commit already exists
                existing = self.memory_repo.get_commit_by_hash(repository_id, commit.hexsha)
                if existing:
                    continue

                parent_hash = commit.parents[0].hexsha if commit.parents else None

                # Get tags for this commit
                commit_tags = []
                for tag in repo.tags:
                    try:
                        if tag.commit.hexsha == commit.hexsha:
                            commit_tags.append(tag.name)
                    except Exception:
                        continue

                committed_at = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)

                self.memory_repo.create_commit(
                    repository_id=repository_id,
                    commit_hash=commit.hexsha,
                    parent_hash=parent_hash,
                    author_name=commit.author.name if commit.author else None,
                    author_email=commit.author.email if commit.author else None,
                    committed_at=committed_at,
                    message=commit.message.strip() if commit.message else None,
                    branch=branch,
                    tags=",".join(commit_tags) if commit_tags else None,
                )
                new_commits += 1

        except Exception as e:
            logger.error(f"Error syncing commits for repository {repository_id}: {e}")

        logger.info(f"Synced {new_commits} new commits for repository {repository_id}")
        return new_commits

    def get_current_commit_hash(self, local_path: str) -> str | None:
        """Get the current HEAD commit hash of a local repository."""
        repo_path = Path(local_path)
        if not repo_path.exists() or not (repo_path / ".git").exists():
            return None

        try:
            repo = Repo(str(repo_path))
            return repo.head.commit.hexsha
        except Exception as e:
            logger.warning(f"Could not get commit hash for {local_path}: {e}")
            return None

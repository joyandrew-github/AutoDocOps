import re
from pathlib import Path
from git import Repo, GitCommandError, InvalidGitRepositoryError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GitError(Exception):
    """Base exception for Git operations."""
    pass


class InvalidRepositoryError(GitError):
    """Raised when repository URL is invalid."""
    pass


class AuthenticationError(GitError):
    """Raised when authentication fails."""
    pass


class NetworkError(GitError):
    """Raised when network connection fails."""
    pass


class RepositoryNotFoundError(GitError):
    """Raised when repository is not found."""
    pass


class PermissionDeniedError(GitError):
    """Raised when permission is denied."""
    pass


class GitManager:
    """Manages Git repository clone and pull operations."""

    def __init__(self, workspace_dir: str | None = None):
        self.workspace_dir = Path(workspace_dir or settings.REPOSITORY_WORKSPACE)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def validate_url(self, url: str) -> bool:
        """Validate that the URL is a valid Git HTTPS URL."""
        pattern = r"^https?://.+/.+$"
        return bool(re.match(pattern, url))

    def extract_repo_name(self, url: str) -> str:
        """Extract repository name from URL."""
        name = url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def get_local_path(self, url: str) -> Path:
        """Get the local path for a repository."""
        owner = url.rstrip("/").split("/")[-2]
        name = self.extract_repo_name(url)
        return self.workspace_dir / owner / name

    def clone_or_pull(self, url: str) -> tuple[Path, str | None]:
        """Clone a repository or pull latest changes if it already exists.

        Returns:
            Tuple of (local_path, default_branch)
        """
        if not self.validate_url(url):
            raise InvalidRepositoryError(f"Invalid repository URL: {url}")

        local_path = self.get_local_path(url)

        try:
            if local_path.exists() and (local_path / ".git").exists():
                return self._pull(local_path, url)
            else:
                return self._clone(url, local_path)
        except GitCommandError as e:
            self._handle_git_error(e, url)
            raise  # unreachable but satisfies type checker

    def _clone(self, url: str, local_path: Path) -> tuple[Path, str | None]:
        """Clone a repository."""
        logger.info(f"Cloning repository: {url} -> {local_path}")
        local_path.mkdir(parents=True, exist_ok=True)
        repo = Repo.clone_from(url, str(local_path), progress=None)
        default_branch = self._get_default_branch(repo)
        logger.info(f"Clone completed. Branch: {default_branch}")
        return local_path, default_branch

    def _pull(self, local_path: Path, url: str) -> tuple[Path, str | None]:
        """Pull latest changes for an existing repository."""
        logger.info(f"Pulling latest changes: {local_path}")
        try:
            repo = Repo(str(local_path))
        except InvalidGitRepositoryError:
            logger.warning(f"Invalid git repo at {local_path}, re-cloning")
            import shutil
            shutil.rmtree(local_path)
            return self._clone(url, local_path)

        origin = repo.remote("origin")
        origin.pull()
        default_branch = self._get_default_branch(repo)
        logger.info(f"Pull completed. Branch: {default_branch}")
        return local_path, default_branch

    def _get_default_branch(self, repo: Repo) -> str | None:
        """Get the default branch name."""
        try:
            return repo.active_branch.name
        except TypeError:
            return None

    def _handle_git_error(self, error: GitCommandError, url: str) -> None:
        """Map GitCommandError to specific exceptions."""
        stderr = str(error.stderr).lower() if error.stderr else ""
        status = error.status

        if "authentication" in stderr or "403" in stderr:
            raise AuthenticationError(f"Authentication failed for {url}: {error}")
        elif "not found" in stderr or "404" in stderr or status == 128:
            raise RepositoryNotFoundError(f"Repository not found: {url}")
        elif "permission denied" in stderr or "permission" in stderr:
            raise PermissionDeniedError(f"Permission denied for {url}: {error}")
        elif "could not resolve" in stderr or "unable to access" in stderr:
            raise NetworkError(f"Network error accessing {url}: {error}")
        else:
            raise GitError(f"Git error for {url}: {error}")

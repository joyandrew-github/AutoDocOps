"""BaseConnector — abstract interface for all integration connectors."""
from __future__ import annotations
import time
import urllib.request
import urllib.error
import json
from abc import ABC, abstractmethod
from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = 1.0  # seconds, exponential
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX_REQUESTS = 60


class RateLimiter:
    """Simple in-memory sliding-window rate limiter per connector instance."""

    def __init__(self, max_requests: int = RATE_LIMIT_MAX_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.max_requests = max_requests
        self.window = window
        self._timestamps: list[float] = []

    def acquire(self) -> bool:
        now = time.time()
        self._timestamps = [t for t in self._timestamps if now - t < self.window]
        if len(self._timestamps) >= self.max_requests:
            return False
        self._timestamps.append(now)
        return True

    def wait_and_acquire(self) -> None:
        while not self.acquire():
            time.sleep(0.5)


class RetryPolicy:
    """Configurable retry with exponential backoff."""

    def __init__(self, max_retries: int = MAX_RETRIES, backoff: float = RETRY_BACKOFF):
        self.max_retries = max_retries
        self.backoff = backoff

    def execute(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        last_err: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    sleep_time = self.backoff * (2 ** attempt)
                    logger.warning(f"Retry {attempt+1}/{self.max_retries} after {sleep_time:.1f}s: {e}")
                    time.sleep(sleep_time)
        raise last_err  # type: ignore[misc]


class BaseConnector(ABC):
    """Abstract base for all integration connectors."""

    connector_type: str = ""
    display_name: str = ""
    supported_auth_methods: list[str] = []
    supported_actions: list[str] = []

    def __init__(self, config: dict[str, Any] | None = None, credentials: dict[str, str] | None = None, base_url: str | None = None):
        self.config = config or {}
        self.credentials = credentials or {}
        self.base_url = (base_url or "").rstrip("/")
        self.rate_limiter = RateLimiter()
        self.retry_policy = RetryPolicy()

    @abstractmethod
    def test_connection(self) -> dict[str, Any]:
        """Test connectivity. Returns {"ok": bool, "message": str}."""
        ...

    @abstractmethod
    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Perform a sync action. Returns result dict."""
        ...

    def get_capabilities(self) -> dict[str, Any]:
        """Return connector capabilities."""
        return {
            "type": self.connector_type,
            "display_name": self.display_name,
            "auth_methods": self.supported_auth_methods,
            "actions": self.supported_actions,
        }

    # ---- HTTP helpers ----

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
        token = self.credentials.get("api_key") or self.credentials.get("token") or self.credentials.get("personal_access_token")
        if token:
            h["Authorization"] = f"Bearer {token}"
        if self.credentials.get("username") and self.credentials.get("password"):
            import base64
            cred = base64.b64encode(f'{self.credentials["username"]}:{self.credentials["password"]}'.encode()).decode()
            h["Authorization"] = f"Basic {cred}"
        return h

    def _request(self, method: str, url: str, body: dict | None = None) -> tuple[int, Any]:
        """Make an HTTP request with rate limiting and retries."""
        def _do_request() -> tuple[int, Any]:
            self.rate_limiter.wait_and_acquire()
            data = json.dumps(body).encode() if body else None
            req = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw = resp.read().decode()
                    try:
                        return resp.status, json.loads(raw)
                    except json.JSONDecodeError:
                        return resp.status, raw
            except urllib.error.HTTPError as e:
                try:
                    err_data = json.loads(e.read().decode())
                except Exception:
                    err_data = {"detail": str(e)}
                return e.code, err_data

        return self.retry_policy.execute(_do_request)

    def _get(self, path: str) -> tuple[int, Any]:
        return self._request("GET", f"{self.base_url}{path}")

    def _post(self, path: str, body: dict | None = None) -> tuple[int, Any]:
        return self._request("POST", f"{self.base_url}{path}", body)

    def _put(self, path: str, body: dict | None = None) -> tuple[int, Any]:
        return self._request("PUT", f"{self.base_url}{path}", body)

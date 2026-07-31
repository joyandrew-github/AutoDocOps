"""HTTP client for benchmark API calls with timing."""
from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
from typing import Any


class BenchmarkHttpClient:
    """Lightweight HTTP client that measures request duration."""

    def __init__(self, base_url: str, token: str | None = None, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def get(self, path: str) -> tuple[int, Any, float]:
        """GET request. Returns (status, data, duration_seconds)."""
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers=self._headers(), method="GET")
        return self._execute(req)

    def post(self, path: str, body: dict | None = None) -> tuple[int, Any, float]:
        """POST request. Returns (status, data, duration_seconds)."""
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(), method="POST")
        return self._execute(req)

    def _execute(self, req: urllib.request.Request) -> tuple[int, Any, float]:
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                duration = time.perf_counter() - start
                raw = resp.read().decode()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    data = raw
                return resp.status, data, duration
        except urllib.error.HTTPError as e:
            duration = time.perf_counter() - start
            try:
                data = json.loads(e.read().decode())
            except Exception:
                data = {"detail": str(e)}
            return e.code, data, duration
        except Exception as e:
            duration = time.perf_counter() - start
            return 0, {"error": str(e)}, duration

    def timed_get(self, path: str, label: str = "") -> dict[str, Any]:
        """GET with structured timing result."""
        status, data, duration = self.get(path)
        return {"label": label or path, "status": status, "data": data, "duration": duration, "ok": 200 <= status < 300}

    def timed_post(self, path: str, body: dict | None = None, label: str = "") -> dict[str, Any]:
        """POST with structured timing result."""
        status, data, duration = self.post(path, body)
        return {"label": label or path, "status": status, "data": data, "duration": duration, "ok": 200 <= status < 300}

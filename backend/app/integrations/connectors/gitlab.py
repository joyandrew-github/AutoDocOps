"""GitLab connector — repo sync, pipeline triggers, build status."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class GitLabConnector(BaseConnector):
    connector_type = "gitlab"
    display_name = "GitLab"
    supported_auth_methods = ["personal_access_token", "oauth2", "api_key"]
    supported_actions = ["test", "sync", "trigger_pipeline", "build_status", "repo_sync"]

    def _headers(self) -> dict[str, str]:
        h = super()._headers()
        token = self.credentials.get("personal_access_token") or self.credentials.get("token", "")
        if token:
            h["PRIVATE-TOKEN"] = token
            h.pop("Authorization", None)
        return h

    def test_connection(self) -> dict[str, Any]:
        try:
            status, data = self._get("/api/v4/user")
            if status == 200:
                return {"ok": True, "message": f"Connected as {data.get('username', 'unknown')}"}
            return {"ok": False, "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "sync")
        if action == "trigger_pipeline":
            return self._trigger_pipeline(payload)
        elif action == "build_status":
            return self._build_status(payload)
        elif action == "repo_sync":
            return self._repo_sync(payload)
        return self._sync_projects(payload)

    def _sync_projects(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            status, data = self._get("/api/v4/projects?membership=true&per_page=50")
            if status == 200 and isinstance(data, list):
                return {"status": "success", "projects_synced": len(data)}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _trigger_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id", self.config.get("project_id", ""))
        ref = payload.get("ref", "main")
        try:
            status, data = self._post(f"/api/v4/projects/{project_id}/pipeline", {"ref": ref})
            return {"status": "success" if status in (200, 201) else "error", "pipeline_id": data.get("id"), "message": str(data)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _build_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        project_id = payload.get("project_id", self.config.get("project_id", ""))
        try:
            status, data = self._get(f"/api/v4/projects/{project_id}/pipelines?per_page=10")
            if status == 200 and isinstance(data, list):
                return {"status": "success", "pipelines": [{"id": p.get("id"), "status": p.get("status"), "ref": p.get("ref")} for p in data[:10]]}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _repo_sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            status, data = self._get("/api/v4/projects?membership=true&per_page=50")
            if status == 200 and isinstance(data, list):
                return {"status": "success", "repos_synced": len(data), "repos": [{"name": r.get("name"), "url": r.get("http_url_to_repo")} for r in data]}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

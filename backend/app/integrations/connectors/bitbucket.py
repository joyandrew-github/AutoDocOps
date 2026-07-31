"""Bitbucket connector — repo sync, pipeline triggers, build status."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class BitbucketConnector(BaseConnector):
    connector_type = "bitbucket"
    display_name = "Bitbucket"
    supported_auth_methods = ["basic", "oauth2", "api_key"]
    supported_actions = ["test", "sync", "trigger_pipeline", "build_status", "repo_sync"]

    def test_connection(self) -> dict[str, Any]:
        try:
            status, data = self._get("/2.0/user")
            if status == 200:
                return {"ok": True, "message": f"Connected as {data.get('display_name', 'unknown')}"}
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
        return self._sync_repos(payload)

    def _sync_repos(self, payload: dict[str, Any]) -> dict[str, Any]:
        workspace = self.config.get("workspace", "")
        try:
            status, data = self._get(f"/2.0/repositories/{workspace}?pagelen=50")
            if status == 200:
                repos = data.get("values", [])
                return {"status": "success", "repos_synced": len(repos)}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _trigger_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
        workspace = self.config.get("workspace", "")
        repo_slug = payload.get("repo_slug", self.config.get("repo_slug", ""))
        body = {"target": {"ref_type": "branch", "type": "pipeline_ref_target", "ref_name": payload.get("branch", "main")}}
        try:
            status, data = self._post(f"/2.0/repositories/{workspace}/{repo_slug}/pipelines/", body)
            return {"status": "success" if status in (200, 201) else "error", "pipeline_uuid": data.get("uuid"), "message": str(data)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _build_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        workspace = self.config.get("workspace", "")
        repo_slug = payload.get("repo_slug", self.config.get("repo_slug", ""))
        try:
            status, data = self._get(f"/2.0/repositories/{workspace}/{repo_slug}/pipelines/?pagelen=10&sort=-created_on")
            if status == 200:
                pipelines = data.get("values", [])
                return {"status": "success", "pipelines": [{"uuid": p.get("uuid"), "state": p.get("state", {}).get("name")} for p in pipelines[:10]]}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _repo_sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._sync_repos(payload)

"""Azure DevOps connector — repo sync, pipeline triggers, build status."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class AzureDevOpsConnector(BaseConnector):
    connector_type = "azure_devops"
    display_name = "Azure DevOps"
    supported_auth_methods = ["personal_access_token", "oauth2"]
    supported_actions = ["test", "sync", "trigger_pipeline", "build_status", "repo_sync"]

    def _headers(self) -> dict[str, str]:
        h = super()._headers()
        token = self.credentials.get("personal_access_token") or self.credentials.get("token", "")
        if token:
            import base64
            cred = base64.b64encode(f":{token}".encode()).decode()
            h["Authorization"] = f"Basic {cred}"
        return h

    def test_connection(self) -> dict[str, Any]:
        org = self.config.get("organization", "")
        try:
            status, data = self._get(f"/{org}/_apis/projects?api-version=7.1")
            if status == 200:
                count = data.get("count", 0)
                return {"ok": True, "message": f"Connected to {org} ({count} projects)"}
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
        org = self.config.get("organization", "")
        try:
            status, data = self._get(f"/{org}/_apis/projects?api-version=7.1")
            if status == 200:
                projects = data.get("value", [])
                return {"status": "success", "projects_synced": len(projects)}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _trigger_pipeline(self, payload: dict[str, Any]) -> dict[str, Any]:
        org = self.config.get("organization", "")
        project = payload.get("project", self.config.get("project", ""))
        pipeline_id = payload.get("pipeline_id", "")
        body = {"resources": {"repositories": {"self": {"refName": payload.get("branch", "refs/heads/main")}}}}
        try:
            status, data = self._post(f"/{org}/{project}/_apis/pipelines/{pipeline_id}/runs?api-version=7.1", body)
            return {"status": "success" if status in (200, 201) else "error", "run_id": data.get("id"), "message": str(data)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _build_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        org = self.config.get("organization", "")
        project = payload.get("project", self.config.get("project", ""))
        try:
            status, data = self._get(f"/{org}/{project}/_apis/build/builds?$top=10&api-version=7.1")
            if status == 200:
                builds = data.get("value", [])
                return {"status": "success", "builds": [{"id": b.get("id"), "status": b.get("status"), "result": b.get("result")} for b in builds[:10]]}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _repo_sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        org = self.config.get("organization", "")
        project = payload.get("project", self.config.get("project", ""))
        try:
            status, data = self._get(f"/{org}/{project}/_apis/git/repositories?api-version=7.1")
            if status == 200:
                repos = data.get("value", [])
                return {"status": "success", "repos_synced": len(repos), "repos": [{"name": r.get("name"), "url": r.get("remoteUrl")} for r in repos]}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

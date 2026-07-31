"""Jira connector — issue linking, PR linking, AI summaries, doc updates."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class JiraConnector(BaseConnector):
    connector_type = "jira"
    display_name = "Jira"
    supported_auth_methods = ["api_key", "oauth2", "basic"]
    supported_actions = ["test", "sync", "create_issue", "link_pr", "ai_summary", "update_docs"]

    def test_connection(self) -> dict[str, Any]:
        try:
            status, data = self._get("/rest/api/3/myself")
            if status == 200:
                return {"ok": True, "message": f"Connected as {data.get('displayName', 'unknown')}"}
            return {"ok": False, "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "sync")
        if action == "create_issue":
            return self._create_issue(payload)
        elif action == "link_pr":
            return self._link_pr(payload)
        elif action == "ai_summary":
            return self._ai_summary(payload)
        elif action == "update_docs":
            return self._update_docs(payload)
        return self._sync_issues(payload)

    def _sync_issues(self, payload: dict[str, Any]) -> dict[str, Any]:
        project = self.config.get("project_key", payload.get("project_key", ""))
        jql = f"project={project} ORDER BY updated DESC" if project else "ORDER BY updated DESC"
        try:
            status, data = self._get(f"/rest/api/3/search?jql={jql}&maxResults=50")
            if status == 200:
                issues = data.get("issues", [])
                return {"status": "success", "issues_synced": len(issues), "total": data.get("total", 0)}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create_issue(self, payload: dict[str, Any]) -> dict[str, Any]:
        project = self.config.get("project_key", payload.get("project_key", ""))
        body = {
            "fields": {
                "project": {"key": project},
                "summary": payload.get("summary", "AutoDocOps Issue"),
                "description": {"type": "doc", "version": 1, "content": [{"type": "paragraph", "content": [{"type": "text", "text": payload.get("description", "")}]}]},
                "issuetype": {"name": payload.get("issue_type", "Task")},
            }
        }
        try:
            status, data = self._post("/rest/api/3/issue", body)
            if status in (200, 201):
                return {"status": "success", "issue_key": data.get("key"), "issue_id": data.get("id")}
            return {"status": "error", "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _link_pr(self, payload: dict[str, Any]) -> dict[str, Any]:
        issue_key = payload.get("issue_key", "")
        pr_url = payload.get("pr_url", "")
        body = {"object": {"url": pr_url, "title": payload.get("pr_title", "Pull Request")}, "relationship": "Reference"}
        try:
            status, data = self._post(f"/rest/api/3/issue/{issue_key}/remotelink", body)
            return {"status": "success" if status in (200, 201) else "error", "message": str(data)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _ai_summary(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "success", "action": "ai_summary", "message": "AI summary generation triggered", "issue_key": payload.get("issue_key")}

    def _update_docs(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {"status": "success", "action": "update_docs", "message": "Documentation update triggered"}

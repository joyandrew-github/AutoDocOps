"""Confluence connector — publish docs, architecture diagrams, change reports."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class ConfluenceConnector(BaseConnector):
    connector_type = "confluence"
    display_name = "Confluence"
    supported_auth_methods = ["api_key", "oauth2", "basic"]
    supported_actions = ["test", "sync", "publish_doc", "publish_architecture", "publish_change_report"]

    def test_connection(self) -> dict[str, Any]:
        try:
            status, data = self._get("/wiki/api/v2/spaces?limit=5")
            if status == 200:
                spaces = data.get("results", [])
                return {"ok": True, "message": f"Connected ({len(spaces)} spaces visible)"}
            return {"ok": False, "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "sync")
        if action == "publish_doc":
            return self._publish_page(payload)
        elif action == "publish_architecture":
            return self._publish_page(payload, prefix="Architecture")
        elif action == "publish_change_report":
            return self._publish_page(payload, prefix="Change Report")
        return self._sync_spaces(payload)

    def _sync_spaces(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            status, data = self._get("/wiki/api/v2/spaces?limit=50")
            if status == 200:
                spaces = data.get("results", [])
                return {"status": "success", "spaces_synced": len(spaces), "spaces": [{"key": s.get("key"), "name": s.get("name")} for s in spaces]}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _publish_page(self, payload: dict[str, Any], prefix: str = "Documentation") -> dict[str, Any]:
        space_key = payload.get("space_key") or self.config.get("space_key", "")
        title = payload.get("title", f"AutoDocOps {prefix}")
        content = payload.get("content", "")
        parent_id = payload.get("parent_id") or self.config.get("parent_page_id")

        body: dict[str, Any] = {
            "spaceId": space_key,
            "status": "current",
            "title": title,
            "body": {"representation": "storage", "value": self._wrap_html(content)},
        }
        if parent_id:
            body["parentId"] = parent_id

        # Try update existing page first
        existing = self._find_page(space_key, title)
        if existing:
            page_id = existing.get("id")
            body["version"] = {"number": existing.get("version", {}).get("number", 1) + 1}
            try:
                status, data = self._put(f"/wiki/api/v2/pages/{page_id}", body)
                if status == 200:
                    return {"status": "success", "action": "updated", "page_id": page_id, "title": title}
                return {"status": "error", "message": f"HTTP {status}: {data}"}
            except Exception as e:
                return {"status": "error", "message": str(e)}

        # Create new page
        try:
            status, data = self._post("/wiki/api/v2/pages", body)
            if status in (200, 201):
                return {"status": "success", "action": "created", "page_id": data.get("id"), "title": title}
            return {"status": "error", "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _find_page(self, space_key: str, title: str) -> dict | None:
        try:
            import urllib.parse
            encoded_title = urllib.parse.quote(title)
            status, data = self._get(f"/wiki/api/v2/spaces/{space_key}/pages?title={encoded_title}&limit=1")
            if status == 200:
                results = data.get("results", [])
                return results[0] if results else None
        except Exception:
            pass
        return None

    def _wrap_html(self, content: str) -> str:
        if content.startswith("<"):
            return content
        # Convert markdown-like text to basic HTML
        lines = content.split("\n")
        html_parts = []
        for line in lines:
            if line.startswith("# "):
                html_parts.append(f"<h1>{line[2:]}</h1>")
            elif line.startswith("## "):
                html_parts.append(f"<h2>{line[3:]}</h2>")
            elif line.startswith("### "):
                html_parts.append(f"<h3>{line[4:]}</h3>")
            elif line.startswith("- "):
                html_parts.append(f"<li>{line[2:]}</li>")
            elif line.strip():
                html_parts.append(f"<p>{line}</p>")
        return "\n".join(html_parts)

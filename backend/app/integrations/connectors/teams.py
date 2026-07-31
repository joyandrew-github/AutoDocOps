"""Microsoft Teams connector — AI notifications, pipeline completion, risk alerts, PR summaries."""
from __future__ import annotations
import json
import urllib.request
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class TeamsConnector(BaseConnector):
    connector_type = "teams"
    display_name = "Microsoft Teams"
    supported_auth_methods = ["webhook", "oauth2"]
    supported_actions = ["test", "sync", "notify", "ai_notification", "pipeline_complete", "risk_alert", "pr_summary"]

    def test_connection(self) -> dict[str, Any]:
        webhook_url = self.credentials.get("webhook_url", "")
        if not webhook_url:
            return {"ok": False, "message": "No webhook URL configured"}
        return {"ok": True, "message": "Webhook URL configured"}

    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "notify")
        return self._send_notification(payload, action)

    def _send_notification(self, payload: dict[str, Any], notification_type: str) -> dict[str, Any]:
        webhook_url = self.credentials.get("webhook_url", "")
        if not webhook_url:
            return {"status": "error", "message": "No webhook URL configured"}

        title = payload.get("title", notification_type.replace("_", " ").title())
        text = payload.get("text", payload.get("message", ""))
        color_map = {"risk_alert": "FF0000", "pipeline_complete": "36A64F", "ai_notification": "4A90D9", "pr_summary": "7C3AED", "notify": "0078D4"}

        card = {
            "type": "message",
            "attachments": [{
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {"type": "TextBlock", "text": f"AutoDocOps — {title}", "weight": "Bolder", "size": "Medium", "color": "Accent"},
                        {"type": "TextBlock", "text": text, "wrap": True},
                    ],
                },
            }],
        }
        if payload.get("details"):
            card["attachments"][0]["content"]["body"].append({"type": "TextBlock", "text": payload["details"], "fontType": "Monospace", "wrap": True})

        try:
            req = urllib.request.Request(webhook_url, data=json.dumps(card).encode(), headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"status": "success", "message": "Teams notification delivered"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

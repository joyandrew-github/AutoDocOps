"""Slack connector — AI notifications, pipeline completion, risk alerts, PR summaries."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class SlackConnector(BaseConnector):
    connector_type = "slack"
    display_name = "Slack"
    supported_auth_methods = ["api_key", "oauth2", "webhook"]
    supported_actions = ["test", "sync", "notify", "ai_notification", "pipeline_complete", "risk_alert", "pr_summary"]

    def _headers(self) -> dict[str, str]:
        h = super()._headers()
        token = self.credentials.get("bot_token") or self.credentials.get("token") or self.credentials.get("api_key", "")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def test_connection(self) -> dict[str, Any]:
        if self.credentials.get("webhook_url"):
            return {"ok": True, "message": "Webhook URL configured"}
        try:
            status, data = self._get("/api/auth.test")
            if status == 200 and data.get("ok"):
                return {"ok": True, "message": f"Connected as {data.get('user', 'bot')} in {data.get('team', 'workspace')}"}
            return {"ok": False, "message": data.get("error", f"HTTP {status}")}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "notify")
        if action == "ai_notification":
            return self._send_notification(payload, "ai_notification")
        elif action == "pipeline_complete":
            return self._send_notification(payload, "pipeline_complete")
        elif action == "risk_alert":
            return self._send_notification(payload, "risk_alert")
        elif action == "pr_summary":
            return self._send_notification(payload, "pr_summary")
        return self._send_notification(payload, "notification")

    def _send_notification(self, payload: dict[str, Any], notification_type: str) -> dict[str, Any]:
        channel = payload.get("channel") or self.config.get("channel", "#general")
        text = payload.get("text", payload.get("message", ""))

        blocks = self._build_blocks(notification_type, payload)

        webhook_url = self.credentials.get("webhook_url")
        if webhook_url:
            return self._send_webhook(webhook_url, text, blocks)

        body = {"channel": channel, "text": text}
        if blocks:
            body["blocks"] = blocks
        try:
            status, data = self._post("/api/chat.postMessage", body)
            if status == 200 and data.get("ok"):
                return {"status": "success", "channel": channel, "ts": data.get("ts")}
            return {"status": "error", "message": data.get("error", f"HTTP {status}")}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _send_webhook(self, url: str, text: str, blocks: list | None) -> dict[str, Any]:
        import json
        import urllib.request
        body: dict[str, Any] = {"text": text}
        if blocks:
            body["blocks"] = blocks
        req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return {"status": "success", "message": "Webhook delivered"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _build_blocks(self, notification_type: str, payload: dict[str, Any]) -> list[dict]:
        title = payload.get("title", notification_type.replace("_", " ").title())
        text = payload.get("text", payload.get("message", ""))
        color_map = {"risk_alert": "#ff0000", "pipeline_complete": "#36a64f", "ai_notification": "#4a90d9", "pr_summary": "#7c3aed"}
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": f"AutoDocOps — {title}"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        ]
        if payload.get("details"):
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"```{payload['details']}```"}})
        return blocks

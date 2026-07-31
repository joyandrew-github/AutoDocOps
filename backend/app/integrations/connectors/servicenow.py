"""ServiceNow connector — incident creation, change requests, CMDB updates."""
from __future__ import annotations
from typing import Any
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry


@ConnectorRegistry.register
class ServiceNowConnector(BaseConnector):
    connector_type = "servicenow"
    display_name = "ServiceNow"
    supported_auth_methods = ["basic", "oauth2", "api_key"]
    supported_actions = ["test", "sync", "create_incident", "create_change_request", "update_cmdb"]

    def test_connection(self) -> dict[str, Any]:
        try:
            status, data = self._get("/api/now/table/sys_user?sysparm_limit=1")
            if status == 200:
                return {"ok": True, "message": "Connected to ServiceNow instance"}
            return {"ok": False, "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def sync(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = payload.get("action", "sync")
        if action == "create_incident":
            return self._create_incident(payload)
        elif action == "create_change_request":
            return self._create_change_request(payload)
        elif action == "update_cmdb":
            return self._update_cmdb(payload)
        return self._sync_incidents(payload)

    def _sync_incidents(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            status, data = self._get("/api/now/table/incident?sysparm_limit=50&sysparm_query=ORDERBYDESCsys_updated_on")
            if status == 200:
                incidents = data.get("result", [])
                return {"status": "success", "incidents_synced": len(incidents)}
            return {"status": "error", "message": f"HTTP {status}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "short_description": payload.get("summary", "AutoDocOps Alert"),
            "description": payload.get("description", ""),
            "urgency": str(payload.get("urgency", "3")),
            "impact": str(payload.get("impact", "3")),
            "category": payload.get("category", "Software"),
            "assignment_group": self.config.get("assignment_group", ""),
        }
        try:
            status, data = self._post("/api/now/table/incident", body)
            if status in (200, 201):
                result = data.get("result", data)
                return {"status": "success", "incident_number": result.get("number"), "sys_id": result.get("sys_id")}
            return {"status": "error", "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _create_change_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = {
            "short_description": payload.get("summary", "AutoDocOps Change"),
            "description": payload.get("description", ""),
            "type": payload.get("change_type", "Normal"),
            "category": payload.get("category", "Software"),
            "assignment_group": self.config.get("assignment_group", ""),
        }
        try:
            status, data = self._post("/api/now/table/change_request", body)
            if status in (200, 201):
                result = data.get("result", data)
                return {"status": "success", "change_number": result.get("number"), "sys_id": result.get("sys_id")}
            return {"status": "error", "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _update_cmdb(self, payload: dict[str, Any]) -> dict[str, Any]:
        ci_name = payload.get("ci_name", "")
        body = {
            "name": ci_name,
            "short_description": payload.get("description", ""),
            "operational_status": payload.get("status", "1"),
        }
        try:
            status, data = self._post("/api/now/table/cmdb_ci", body)
            if status in (200, 201):
                result = data.get("result", data)
                return {"status": "success", "sys_id": result.get("sys_id"), "ci_name": ci_name}
            return {"status": "error", "message": f"HTTP {status}: {data}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

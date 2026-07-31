"""IntegrationService — orchestrates connector lifecycle and sync operations."""
from __future__ import annotations
import time
from typing import Any
from sqlalchemy.orm import Session
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry
from app.integrations.repository import IntegrationRepository
from app.models.integration import Integration
from app.core.logging import get_logger

# Ensure all connectors are registered
import app.integrations.connectors  # noqa: F401

logger = get_logger(__name__)


class IntegrationService:
    """High-level API for managing integrations."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = IntegrationRepository(db)

    # ---- Connect ----

    def connect(
        self,
        user_id: int,
        integration_type: str,
        name: str,
        auth_method: str = "api_key",
        base_url: str | None = None,
        credentials: dict[str, str] | None = None,
        config: dict[str, Any] | None = None,
        repository_id: int | None = None,
    ) -> dict[str, Any]:
        """Create a new integration and test connectivity."""
        # Validate connector type
        try:
            ConnectorRegistry.get(integration_type)
        except ValueError as e:
            return {"status": "error", "message": str(e)}

        # Create DB record
        integration = self.repo.create(
            user_id=user_id,
            integration_type=integration_type,
            name=name,
            auth_method=auth_method,
            base_url=base_url,
            credentials=credentials,
            config=config,
            repository_id=repository_id,
        )

        # Test connection
        connector = self._create_connector(integration)
        start = time.time()
        try:
            result = connector.test_connection()
            duration_ms = int((time.time() - start) * 1000)
            if result.get("ok"):
                self.repo.update_status(integration, "active")
                self.repo.create_log(integration.id, "connect", "success", result.get("message"), duration_ms=duration_ms)
            else:
                self.repo.update_status(integration, "error", result.get("message"))
                self.repo.create_log(integration.id, "connect", "error", result.get("message"), duration_ms=duration_ms)
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self.repo.update_status(integration, "error", str(e))
            self.repo.create_log(integration.id, "connect", "error", str(e), duration_ms=duration_ms)
            result = {"ok": False, "message": str(e)}

        return {
            "id": integration.id,
            "integration_type": integration_type,
            "name": name,
            "status": integration.status,
            "message": result.get("message", ""),
        }

    # ---- List ----

    def list_integrations(self, user_id: int | None = None) -> list[dict[str, Any]]:
        """List all integrations, optionally filtered by user."""
        if user_id:
            integrations = self.repo.get_by_user(user_id)
        else:
            integrations = self.repo.get_all()
        return [self._to_dict(i) for i in integrations]

    # ---- Sync ----

    def sync(self, integration_id: int, action: str = "sync", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a sync action on an integration."""
        integration = self.repo.get_by_id(integration_id)
        if not integration:
            return {"status": "error", "message": f"Integration not found: {integration_id}"}
        if not integration.is_active:
            return {"status": "error", "message": "Integration is inactive"}

        connector = self._create_connector(integration)
        merged_payload = {**(payload or {}), "action": action}

        start = time.time()
        try:
            result = connector.sync(merged_payload)
            duration_ms = int((time.time() - start) * 1000)
            status = result.get("status", "success")
            if status == "success":
                self.repo.update_status(integration, "active")
            else:
                self.repo.update_status(integration, "error", result.get("message"))
            self.repo.create_log(integration.id, action, status, result.get("message"), details=result, duration_ms=duration_ms)
            return {"integration_id": integration_id, "action": action, "status": status, "message": result.get("message", ""), "details": result, "duration_ms": duration_ms}
        except Exception as e:
            duration_ms = int((time.time() - start) * 1000)
            self.repo.update_status(integration, "error", str(e))
            self.repo.create_log(integration.id, action, "error", str(e), duration_ms=duration_ms)
            return {"integration_id": integration_id, "action": action, "status": "error", "message": str(e), "details": {}, "duration_ms": duration_ms}

    # ---- Status ----

    def get_status(self, integration_id: int) -> dict[str, Any]:
        """Get integration health status."""
        integration = self.repo.get_by_id(integration_id)
        if not integration:
            return {"status": "error", "message": f"Integration not found: {integration_id}"}
        logs = self.repo.get_logs(integration_id, limit=100)
        total = len(logs)
        successes = sum(1 for l in logs if l.status == "success")
        uptime_pct = (successes / total * 100) if total > 0 else 100.0
        return {
            "integration_id": integration.id,
            "integration_type": integration.integration_type,
            "name": integration.name,
            "status": integration.status,
            "is_healthy": integration.status == "active" and integration.is_active,
            "last_sync_at": integration.last_sync_at,
            "last_error": integration.last_error,
            "sync_count": integration.sync_count or 0,
            "uptime_pct": round(uptime_pct, 1),
        }

    # ---- Logs ----

    def get_logs(self, integration_id: int, limit: int = 50) -> list[dict[str, Any]]:
        logs = self.repo.get_logs(integration_id, limit)
        return [
            {
                "id": l.id,
                "integration_id": l.integration_id,
                "event_type": l.event_type,
                "status": l.status,
                "message": l.message,
                "details": l.details,
                "duration_ms": l.duration_ms,
                "created_at": str(l.created_at) if l.created_at else None,
            }
            for l in logs
        ]

    # ---- Available connectors ----

    def available_connectors(self) -> list[dict[str, Any]]:
        return ConnectorRegistry.available()

    # ---- Disconnect ----

    def disconnect(self, integration_id: int) -> dict[str, Any]:
        integration = self.repo.get_by_id(integration_id)
        if not integration:
            return {"status": "error", "message": f"Integration not found: {integration_id}"}
        self.repo.deactivate(integration)
        self.repo.create_log(integration_id, "disconnect", "success", "Integration disconnected")
        return {"status": "success", "message": "Integration disconnected"}

    # ---- Helpers ----

    def _create_connector(self, integration: Integration) -> BaseConnector:
        return ConnectorRegistry.create(
            integration.integration_type,
            config=integration.config or {},
            credentials=integration.credentials or {},
            base_url=integration.base_url or "",
        )

    def _to_dict(self, i: Integration) -> dict[str, Any]:
        return {
            "id": i.id,
            "integration_type": i.integration_type,
            "name": i.name,
            "auth_method": i.auth_method,
            "status": i.status,
            "base_url": i.base_url,
            "config": i.config,
            "repository_id": i.repository_id,
            "last_sync_at": i.last_sync_at,
            "last_error": i.last_error,
            "sync_count": i.sync_count or 0,
            "is_active": i.is_active,
            "created_at": str(i.created_at) if i.created_at else None,
            "updated_at": str(i.updated_at) if i.updated_at else None,
        }

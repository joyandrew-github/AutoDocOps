"""Integration repository — DB operations for integrations and logs."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.integration import Integration, IntegrationLog


class IntegrationRepository:
    """Data access layer for integration models."""

    def __init__(self, db: Session):
        self.db = db

    # ---- Integration CRUD ----

    def create(self, user_id: int, integration_type: str, name: str, auth_method: str,
               base_url: str | None = None, credentials: dict | None = None,
               config: dict | None = None, repository_id: int | None = None) -> Integration:
        integration = Integration(
            user_id=user_id,
            integration_type=integration_type,
            name=name,
            auth_method=auth_method,
            status="pending",
            base_url=base_url,
            credentials=credentials,
            config=config,
            repository_id=repository_id,
        )
        self.db.add(integration)
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def get_by_id(self, integration_id: int) -> Integration | None:
        return self.db.query(Integration).filter(Integration.id == integration_id).first()

    def get_by_user(self, user_id: int) -> list[Integration]:
        return self.db.query(Integration).filter(Integration.user_id == user_id).order_by(Integration.created_at.desc()).all()

    def get_all(self) -> list[Integration]:
        return self.db.query(Integration).order_by(Integration.created_at.desc()).all()

    def get_by_type(self, integration_type: str) -> list[Integration]:
        return self.db.query(Integration).filter(Integration.integration_type == integration_type).all()

    def update_status(self, integration: Integration, status: str, last_error: str | None = None) -> Integration:
        integration.status = status
        integration.last_error = last_error
        if status == "active":
            integration.last_sync_at = datetime.now(timezone.utc).isoformat()
            integration.sync_count = (integration.sync_count or 0) + 1
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def update_config(self, integration: Integration, config: dict) -> Integration:
        integration.config = config
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def deactivate(self, integration: Integration) -> Integration:
        integration.is_active = False
        integration.status = "disconnected"
        self.db.commit()
        self.db.refresh(integration)
        return integration

    def delete(self, integration_id: int) -> bool:
        integration = self.get_by_id(integration_id)
        if not integration:
            return False
        self.db.delete(integration)
        self.db.commit()
        return True

    # ---- Logs ----

    def create_log(self, integration_id: int, event_type: str, status: str,
                   message: str | None = None, details: dict | None = None,
                   duration_ms: int | None = None) -> IntegrationLog:
        log = IntegrationLog(
            integration_id=integration_id,
            event_type=event_type,
            status=status,
            message=message,
            details=details,
            duration_ms=duration_ms,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_logs(self, integration_id: int, limit: int = 50) -> list[IntegrationLog]:
        return (
            self.db.query(IntegrationLog)
            .filter(IntegrationLog.integration_id == integration_id)
            .order_by(IntegrationLog.created_at.desc())
            .limit(limit)
            .all()
        )

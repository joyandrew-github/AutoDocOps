"""Integration models — stores connector configurations and sync state."""
from sqlalchemy import String, Integer, Boolean, Text, JSON, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
import enum


class IntegrationType(str, enum.Enum):
    JIRA = "jira"
    AZURE_DEVOPS = "azure_devops"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
    SLACK = "slack"
    TEAMS = "teams"
    CONFLUENCE = "confluence"
    SERVICENOW = "servicenow"


class AuthMethod(str, enum.Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    PAT = "personal_access_token"
    BASIC = "basic"
    WEBHOOK = "webhook"


class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"
    DISCONNECTED = "disconnected"


class Integration(Base, TimestampMixin):
    """Stores an active integration connection."""

    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    integration_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_method: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    base_url: Mapped[str | None] = mapped_column(String(512))
    # Encrypted credentials stored as JSON
    credentials: Mapped[dict | None] = mapped_column(JSON)
    # Connector-specific config
    config: Mapped[dict | None] = mapped_column(JSON)
    # Link to repo if applicable
    repository_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("repositories.id"))
    # Health
    last_sync_at: Mapped[str | None] = mapped_column(String(50))
    last_error: Mapped[str | None] = mapped_column(Text)
    sync_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Integration(id={self.id}, type={self.integration_type}, name={self.name}, status={self.status})>"


class IntegrationLog(Base, TimestampMixin):
    """Audit log for integration events."""

    __tablename__ = "integration_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    integration_id: Mapped[int] = mapped_column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str | None] = mapped_column(Text)
    details: Mapped[dict | None] = mapped_column(JSON)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

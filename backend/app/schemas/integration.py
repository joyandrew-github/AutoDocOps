"""Pydantic schemas for the integrations API."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any


class IntegrationConnectRequest(BaseModel):
    integration_type: str = Field(..., description="One of: jira, azure_devops, gitlab, bitbucket, slack, teams, confluence, servicenow")
    name: str = Field(..., description="Display name for this integration")
    auth_method: str = Field("api_key", description="Auth method: oauth2, api_key, personal_access_token, basic, webhook")
    base_url: str | None = Field(None, description="Base URL for the service (e.g. https://myorg.atlassian.net)")
    credentials: dict[str, str] = Field(default_factory=dict, description="Auth credentials (api_key, token, username/password, etc.)")
    config: dict[str, Any] = Field(default_factory=dict, description="Connector-specific config (project_key, channel, workspace, etc.)")
    repository_id: int | None = Field(None, description="Optional linked repository ID")


class IntegrationResponse(BaseModel):
    id: int
    integration_type: str
    name: str
    auth_method: str
    status: str
    base_url: str | None = None
    config: dict[str, Any] | None = None
    repository_id: int | None = None
    last_sync_at: str | None = None
    last_error: str | None = None
    sync_count: int = 0
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class IntegrationSyncRequest(BaseModel):
    integration_id: int
    action: str = Field("sync", description="Action: sync, test, publish, notify")
    payload: dict[str, Any] = Field(default_factory=dict, description="Action-specific payload")


class IntegrationSyncResponse(BaseModel):
    integration_id: int
    action: str
    status: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0


class IntegrationStatusResponse(BaseModel):
    integration_id: int
    integration_type: str
    name: str
    status: str
    is_healthy: bool
    last_sync_at: str | None = None
    last_error: str | None = None
    sync_count: int = 0
    uptime_pct: float = 100.0


class IntegrationLogResponse(BaseModel):
    id: int
    integration_id: int
    event_type: str
    status: str
    message: str | None = None
    details: dict[str, Any] | None = None
    duration_ms: int | None = None
    created_at: str | None = None

    model_config = {"from_attributes": True}

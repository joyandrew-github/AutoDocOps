"""Integration API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.integrations.service import IntegrationService
from app.schemas.integration import (
    IntegrationConnectRequest,
    IntegrationResponse,
    IntegrationSyncRequest,
    IntegrationSyncResponse,
    IntegrationStatusResponse,
    IntegrationLogResponse,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _service(db: Session = Depends(get_db)) -> IntegrationService:
    return IntegrationService(db)


@router.post("/connect", response_model=dict)
def connect_integration(req: IntegrationConnectRequest, svc: IntegrationService = Depends(_service)):
    """Connect a new integration."""
    return svc.connect(
        user_id=1,  # TODO: extract from auth context
        integration_type=req.integration_type,
        name=req.name,
        auth_method=req.auth_method,
        base_url=req.base_url,
        credentials=req.credentials,
        config=req.config,
        repository_id=req.repository_id,
    )


@router.get("", response_model=list[dict])
def list_integrations(user_id: int | None = None, svc: IntegrationService = Depends(_service)):
    """List all integrations."""
    return svc.list_integrations(user_id)


@router.get("/connectors", response_model=list[dict])
def list_connectors(svc: IntegrationService = Depends(_service)):
    """List available connector types."""
    return svc.available_connectors()


@router.post("/sync", response_model=dict)
def sync_integration(req: IntegrationSyncRequest, svc: IntegrationService = Depends(_service)):
    """Execute a sync action on an integration."""
    return svc.sync(
        integration_id=req.integration_id,
        action=req.action,
        payload=req.payload,
    )


@router.get("/{integration_id}/status", response_model=dict)
def get_integration_status(integration_id: int, svc: IntegrationService = Depends(_service)):
    """Get integration health status."""
    return svc.get_status(integration_id)


@router.get("/{integration_id}/logs", response_model=list[dict])
def get_integration_logs(integration_id: int, limit: int = 50, svc: IntegrationService = Depends(_service)):
    """Get integration event logs."""
    return svc.get_logs(integration_id, limit)


@router.post("/{integration_id}/disconnect", response_model=dict)
def disconnect_integration(integration_id: int, svc: IntegrationService = Depends(_service)):
    """Disconnect an integration."""
    return svc.disconnect(integration_id)

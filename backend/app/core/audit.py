from sqlalchemy.orm import Session
from app.models.platform import AuditLog
from app.core.logging import get_logger

logger = get_logger(__name__)


def record_audit(
    db: Session,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    user_id: int | None = None,
    organization_id: int | None = None,
    details: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Record an audit log entry."""
    entry = AuditLog(
        user_id=user_id,
        organization_id=organization_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info(f"Audit: user={user_id} action={action} resource={resource_type}/{resource_id}")
    return entry

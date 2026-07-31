from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.platform import OrganizationMember, RoleType

security_scheme = HTTPBearer(auto_error=False)

ROLE_HIERARCHY = {
    RoleType.ADMIN: 4,
    RoleType.MAINTAINER: 3,
    RoleType.DEVELOPER: 2,
    RoleType.VIEWER: 1,
}


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the current user from JWT token."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """Optional authentication — returns None if no token."""
    if not credentials:
        return None
    payload = decode_access_token(credentials.credentials)
    if not payload:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id), User.is_active == True).first()


class RequireRole:
    """Dependency that enforces minimum role level within an organization."""

    def __init__(self, minimum_role: RoleType):
        self.minimum_role = minimum_role

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        org_id: int | None = None,
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if org_id is None:
            return current_user
        member = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.user_id == current_user.id,
                OrganizationMember.organization_id == org_id,
                OrganizationMember.is_active == True,
            )
            .first()
        )
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")
        user_level = ROLE_HIERARCHY.get(RoleType(member.role), 0)
        required_level = ROLE_HIERARCHY.get(self.minimum_role, 0)
        if user_level < required_level:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {self.minimum_role.value} role or higher")
        return current_user


require_admin = RequireRole(RoleType.ADMIN)
require_maintainer = RequireRole(RoleType.MAINTAINER)
require_developer = RequireRole(RoleType.DEVELOPER)
require_viewer = RequireRole(RoleType.VIEWER)

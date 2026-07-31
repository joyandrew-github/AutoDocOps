from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from app.db.session import get_db
from app.models.user import User
from app.models.platform import RefreshToken
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    create_refresh_token, verify_refresh_token_hash,
)
from app.core.deps import get_current_user
from app.core.config import settings
from app.core.audit import record_audit

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_superuser: bool


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    """Register a new user."""
    if db.query(User).filter((User.email == body.email) | (User.username == body.username)).first():
        raise HTTPException(status_code=400, detail="Email or username already registered")
    user = User(
        email=body.email,
        username=body.username,
        hashed_password=get_password_hash(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_audit(db, "register", "user", str(user.id), user.id, ip_address=request.client.host if request.client else None)
    return UserResponse(id=user.id, email=user.email, username=user.username, full_name=user.full_name, is_active=user.is_active, is_superuser=user.is_superuser)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Authenticate and receive tokens."""
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    access_token = create_access_token(data={"sub": str(user.id)})
    raw_refresh, token_hash = create_refresh_token(data={"sub": str(user.id)})
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_info=request.headers.get("user-agent", "")[:512],
    )
    db.add(db_token)
    db.commit()
    record_audit(db, "login", "user", str(user.id), user.id, ip_address=request.client.host if request.client else None)
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using a refresh token."""
    tokens = db.query(RefreshToken).filter(RefreshToken.is_revoked == False).all()
    matched = None
    for t in tokens:
        if verify_refresh_token_hash(body.refresh_token, t.token_hash):
            matched = t
            break
    if not matched:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if str(matched.expires_at) < str(datetime.now(timezone.utc)):
        matched.is_revoked = True
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expired")
    # Rotate: revoke old, issue new
    matched.is_revoked = True
    user = db.query(User).filter(User.id == matched.user_id).first()
    if not user or not user.is_active:
        db.commit()
        raise HTTPException(status_code=401, detail="User not found or inactive")
    access_token = create_access_token(data={"sub": str(user.id)})
    raw_refresh, token_hash = create_refresh_token(data={"sub": str(user.id)})
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    db_token = RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revoke all refresh tokens for user."""
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id, RefreshToken.is_revoked == False).update({"is_revoked": True})
    db.commit()
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(id=current_user.id, email=current_user.email, username=current_user.username, full_name=current_user.full_name, is_active=current_user.is_active, is_superuser=current_user.is_superuser)

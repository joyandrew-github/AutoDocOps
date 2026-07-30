"""Security helpers — webhook signature validation, token encryption."""
from __future__ import annotations
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _get_fernet() -> Fernet:
    key = settings.SECRET_KEY.encode()
    key = base64.urlsafe_b64encode(key.ljust(32, b"\0")[:32])
    return Fernet(key)


def encrypt_token(token: str) -> str:
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_token(encrypted: str) -> str:
    return _get_fernet().decrypt(encrypted.encode()).decode()


def verify_webhook_signature(payload_body: bytes, signature_header: str, secret: str) -> bool:
    """Validate GitHub webhook HMAC-SHA256 signature."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode(), payload_body, hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)

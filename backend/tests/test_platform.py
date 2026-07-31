"""Integration tests for platform hardening: auth, RBAC, security, caching, audit."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from app.core.security import (
    get_password_hash, verify_password,
    create_access_token, decode_access_token,
    create_refresh_token, verify_refresh_token_hash,
)
from app.core.cache import cache_get, cache_set, cache_delete, cached
from app.core.middleware import RequestIdMiddleware, SecurityHeadersMiddleware
from app.models.platform import RoleType, Organization, OrganizationMember, RefreshToken, AuditLog
from app.core.deps import ROLE_HIERARCHY


# ---- Security Tests ----

class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "secure_password_123"
        hashed = get_password_hash(pw)
        assert hashed != pw
        assert verify_password(pw, hashed)

    def test_wrong_password(self):
        hashed = get_password_hash("correct")
        assert not verify_password("wrong", hashed)


class TestJWT:
    def test_create_and_decode_access_token(self):
        data = {"sub": "42"}
        token = create_access_token(data)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_expired_token(self):
        data = {"sub": "42"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = decode_access_token(token)
        assert payload is None

    def test_invalid_token(self):
        payload = decode_access_token("not.a.valid.token")
        assert payload is None


class TestRefreshToken:
    def test_create_and_verify(self):
        raw, token_hash = create_refresh_token({"sub": "1"})
        assert len(raw) > 30
        assert len(token_hash) == 64
        assert verify_refresh_token_hash(raw, token_hash)

    def test_wrong_token(self):
        _, token_hash = create_refresh_token({"sub": "1"})
        assert not verify_refresh_token_hash("wrong_token", token_hash)


# ---- RBAC Tests ----

class TestRBAC:
    def test_role_hierarchy(self):
        assert ROLE_HIERARCHY[RoleType.ADMIN] > ROLE_HIERARCHY[RoleType.MAINTAINER]
        assert ROLE_HIERARCHY[RoleType.MAINTAINER] > ROLE_HIERARCHY[RoleType.DEVELOPER]
        assert ROLE_HIERARCHY[RoleType.DEVELOPER] > ROLE_HIERARCHY[RoleType.VIEWER]

    def test_role_enum_values(self):
        assert RoleType.ADMIN.value == "admin"
        assert RoleType.VIEWER.value == "viewer"


# ---- Model Tests ----

class TestPlatformModels:
    def test_organization_model(self):
        org = Organization()
        org.name = "TestOrg"
        org.slug = "test-org"
        assert org.name == "TestOrg"

    def test_audit_log_model(self):
        log = AuditLog()
        log.action = "login"
        log.resource_type = "user"
        log.resource_id = "1"
        assert log.action == "login"

    def test_refresh_token_model(self):
        rt = RefreshToken()
        rt.token_hash = "abc123"
        rt.is_revoked = False
        assert not rt.is_revoked


# ---- Cache Tests ----

class TestCaching:
    @patch("app.core.cache.redis_client")
    def test_cache_set_and_get(self, mock_redis):
        mock_client = MagicMock()
        mock_redis.get_client.return_value = mock_client
        mock_client.get.return_value = '{"key": "value"}'
        result = cache_get("test_key")
        assert result == {"key": "value"}

    @patch("app.core.cache.redis_client")
    def test_cache_miss(self, mock_redis):
        mock_client = MagicMock()
        mock_redis.get_client.return_value = mock_client
        mock_client.get.return_value = None
        result = cache_get("missing_key")
        assert result is None

    @patch("app.core.cache.redis_client")
    def test_cache_delete(self, mock_redis):
        mock_client = MagicMock()
        mock_redis.get_client.return_value = mock_client
        cache_delete("test_key")
        mock_client.delete.assert_called_once_with("cache:test_key")

    @patch("app.core.cache.redis_client")
    def test_cache_failure_graceful(self, mock_redis):
        mock_redis.get_client.side_effect = RuntimeError("not connected")
        result = cache_get("key")
        assert result is None


# ---- Middleware Tests ----

class TestMiddleware:
    def test_security_headers_class_exists(self):
        assert SecurityHeadersMiddleware is not None

    def test_request_id_class_exists(self):
        assert RequestIdMiddleware is not None


# ---- Celery Tests ----

class TestCeleryConfig:
    def test_celery_app_import(self):
        from app.core.celery_app import celery_app
        assert celery_app.main == "autodocops"

    def test_worker_tasks_import(self):
        from app.workers.tasks import health_check_task
        assert callable(health_check_task)


# ---- Audit Tests ----

class TestAudit:
    @patch("app.core.audit.get_logger")
    def test_record_audit(self, mock_logger):
        mock_db = MagicMock()
        from app.core.audit import record_audit
        entry = record_audit(
            db=mock_db,
            action="login",
            resource_type="user",
            resource_id="1",
            user_id=1,
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


# ---- Observability Tests ----

class TestObservability:
    def test_prometheus_setup_import(self):
        from app.core.observability import setup_prometheus
        assert callable(setup_prometheus)

    def test_tracing_setup_import(self):
        from app.core.observability import setup_tracing
        assert callable(setup_tracing)


# ---- Auth Endpoint Tests ----

class TestAuthSchemas:
    def test_register_schema(self):
        from app.api.v1.endpoints.auth import RegisterRequest
        req = RegisterRequest(email="a@b.com", username="test", password="pass")
        assert req.username == "test"

    def test_login_schema(self):
        from app.api.v1.endpoints.auth import LoginRequest
        req = LoginRequest(username="test", password="pass")
        assert req.password == "pass"

    def test_token_response_schema(self):
        from app.api.v1.endpoints.auth import TokenResponse
        resp = TokenResponse(access_token="a", refresh_token="b", expires_in=1800)
        assert resp.token_type == "bearer"

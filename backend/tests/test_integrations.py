"""Tests for the enterprise integrations platform."""
import pytest
from unittest.mock import MagicMock, patch

from app.integrations.base import BaseConnector, RateLimiter, RetryPolicy
from app.integrations.registry import ConnectorRegistry
from app.integrations.connectors.jira import JiraConnector
from app.integrations.connectors.azure_devops import AzureDevOpsConnector
from app.integrations.connectors.gitlab import GitLabConnector
from app.integrations.connectors.bitbucket import BitbucketConnector
from app.integrations.connectors.slack import SlackConnector
from app.integrations.connectors.teams import TeamsConnector
from app.integrations.connectors.confluence import ConfluenceConnector
from app.integrations.connectors.servicenow import ServiceNowConnector
from app.integrations.service import IntegrationService
from app.integrations.repository import IntegrationRepository
from app.models.integration import Integration, IntegrationLog, IntegrationType, AuthMethod, IntegrationStatus


# ==================================================================
# Rate Limiter
# ==================================================================

class TestRateLimiter:
    def test_acquire_within_limit(self):
        rl = RateLimiter(max_requests=5, window=60)
        for _ in range(5):
            assert rl.acquire() is True

    def test_acquire_exceeds_limit(self):
        rl = RateLimiter(max_requests=2, window=60)
        assert rl.acquire() is True
        assert rl.acquire() is True
        assert rl.acquire() is False


# ==================================================================
# Retry Policy
# ==================================================================

class TestRetryPolicy:
    def test_success_no_retry(self):
        rp = RetryPolicy(max_retries=3)
        result = rp.execute(lambda: "ok")
        assert result == "ok"

    def test_retry_on_failure(self):
        rp = RetryPolicy(max_retries=2, backoff=0.01)
        call_count = 0
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "ok"
        result = rp.execute(flaky)
        assert result == "ok"
        assert call_count == 3

    def test_exhausted_retries(self):
        rp = RetryPolicy(max_retries=1, backoff=0.01)
        with pytest.raises(ValueError, match="fail"):
            rp.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))


# ==================================================================
# Registry
# ==================================================================

class TestConnectorRegistry:
    def test_all_connectors_registered(self):
        types = ConnectorRegistry.types()
        assert "jira" in types
        assert "azure_devops" in types
        assert "gitlab" in types
        assert "bitbucket" in types
        assert "slack" in types
        assert "teams" in types
        assert "confluence" in types
        assert "servicenow" in types
        assert len(types) == 8

    def test_get_known(self):
        cls = ConnectorRegistry.get("jira")
        assert cls is JiraConnector

    def test_get_unknown(self):
        with pytest.raises(ValueError, match="Unknown connector type"):
            ConnectorRegistry.get("nonexistent")

    def test_create(self):
        connector = ConnectorRegistry.create("slack", credentials={"bot_token": "xoxb-123"})
        assert isinstance(connector, SlackConnector)
        assert connector.credentials["bot_token"] == "xoxb-123"

    def test_available(self):
        avail = ConnectorRegistry.available()
        assert len(avail) == 8
        names = {c["type"] for c in avail}
        assert "jira" in names


# ==================================================================
# Connector capabilities
# ==================================================================

class TestConnectorCapabilities:
    @pytest.fixture(params=["jira", "azure_devops", "gitlab", "bitbucket", "slack", "teams", "confluence", "servicenow"])
    def connector(self, request):
        return ConnectorRegistry.create(request.param)

    def test_has_type(self, connector):
        assert connector.connector_type
        assert connector.display_name

    def test_has_auth_methods(self, connector):
        assert len(connector.supported_auth_methods) > 0

    def test_has_actions(self, connector):
        assert "test" in connector.supported_actions
        assert "sync" in connector.supported_actions

    def test_get_capabilities(self, connector):
        caps = connector.get_capabilities()
        assert "type" in caps
        assert "display_name" in caps
        assert "auth_methods" in caps
        assert "actions" in caps


# ==================================================================
# Individual Connectors (unit tests with mocked HTTP)
# ==================================================================

class TestJiraConnector:
    def test_test_connection_success(self):
        conn = JiraConnector(base_url="https://jira.example.com", credentials={"api_key": "test"})
        with patch.object(conn, '_get', return_value=(200, {"displayName": "John"})):
            result = conn.test_connection()
            assert result["ok"] is True
            assert "John" in result["message"]

    def test_test_connection_failure(self):
        conn = JiraConnector(base_url="https://jira.example.com")
        with patch.object(conn, '_get', return_value=(401, {"error": "Unauthorized"})):
            result = conn.test_connection()
            assert result["ok"] is False

    def test_sync_issues(self):
        conn = JiraConnector(config={"project_key": "PROJ"})
        with patch.object(conn, '_get', return_value=(200, {"issues": [{"key": "PROJ-1"}], "total": 1})):
            result = conn.sync({"action": "sync"})
            assert result["status"] == "success"
            assert result["issues_synced"] == 1

    def test_create_issue(self):
        conn = JiraConnector(config={"project_key": "PROJ"})
        with patch.object(conn, '_post', return_value=(201, {"key": "PROJ-42", "id": "123"})):
            result = conn.sync({"action": "create_issue", "summary": "Test issue"})
            assert result["status"] == "success"
            assert result["issue_key"] == "PROJ-42"


class TestSlackConnector:
    def test_test_connection_webhook(self):
        conn = SlackConnector(credentials={"webhook_url": "https://hooks.slack.com/xxx"})
        result = conn.test_connection()
        assert result["ok"] is True

    def test_test_connection_api(self):
        conn = SlackConnector(base_url="https://slack.com", credentials={"bot_token": "xoxb-123"})
        with patch.object(conn, '_get', return_value=(200, {"ok": True, "user": "bot", "team": "myteam"})):
            result = conn.test_connection()
            assert result["ok"] is True

    def test_send_notification(self):
        conn = SlackConnector(base_url="https://slack.com", credentials={"bot_token": "xoxb-123"}, config={"channel": "#test"})
        with patch.object(conn, '_post', return_value=(200, {"ok": True, "ts": "1234.5678"})):
            result = conn.sync({"action": "notify", "text": "Hello"})
            assert result["status"] == "success"


class TestTeamsConnector:
    def test_test_connection_no_webhook(self):
        conn = TeamsConnector()
        result = conn.test_connection()
        assert result["ok"] is False

    def test_test_connection_with_webhook(self):
        conn = TeamsConnector(credentials={"webhook_url": "https://teams.webhook.url"})
        result = conn.test_connection()
        assert result["ok"] is True


class TestGitLabConnector:
    def test_test_connection(self):
        conn = GitLabConnector(base_url="https://gitlab.com", credentials={"personal_access_token": "glpat-123"})
        with patch.object(conn, '_get', return_value=(200, {"username": "dev"})):
            result = conn.test_connection()
            assert result["ok"] is True

    def test_sync_projects(self):
        conn = GitLabConnector(base_url="https://gitlab.com")
        with patch.object(conn, '_get', return_value=(200, [{"name": "proj1"}, {"name": "proj2"}])):
            result = conn.sync({"action": "sync"})
            assert result["status"] == "success"
            assert result["projects_synced"] == 2


class TestAzureDevOpsConnector:
    def test_test_connection(self):
        conn = AzureDevOpsConnector(base_url="https://dev.azure.com", config={"organization": "myorg"}, credentials={"personal_access_token": "pat"})
        with patch.object(conn, '_get', return_value=(200, {"count": 3})):
            result = conn.test_connection()
            assert result["ok"] is True


class TestConfluenceConnector:
    def test_test_connection(self):
        conn = ConfluenceConnector(base_url="https://myorg.atlassian.net", credentials={"api_key": "key"})
        with patch.object(conn, '_get', return_value=(200, {"results": [{"key": "SPACE1"}]})):
            result = conn.test_connection()
            assert result["ok"] is True

    def test_publish_doc_create(self):
        conn = ConfluenceConnector(config={"space_key": "DOC"})
        with patch.object(conn, '_find_page', return_value=None):
            with patch.object(conn, '_post', return_value=(201, {"id": "123"})):
                result = conn.sync({"action": "publish_doc", "title": "API Docs", "content": "# Hello"})
                assert result["status"] == "success"
                assert result["action"] == "created"


class TestServiceNowConnector:
    def test_test_connection(self):
        conn = ServiceNowConnector(base_url="https://instance.service-now.com", credentials={"username": "admin", "password": "pass"})
        with patch.object(conn, '_get', return_value=(200, {"result": []})):
            result = conn.test_connection()
            assert result["ok"] is True

    def test_create_incident(self):
        conn = ServiceNowConnector(base_url="https://instance.service-now.com")
        with patch.object(conn, '_post', return_value=(201, {"result": {"number": "INC001", "sys_id": "abc"}})):
            result = conn.sync({"action": "create_incident", "summary": "Alert"})
            assert result["status"] == "success"
            assert result["incident_number"] == "INC001"


class TestBitbucketConnector:
    def test_test_connection(self):
        conn = BitbucketConnector(base_url="https://api.bitbucket.org", credentials={"username": "user", "password": "pass"})
        with patch.object(conn, '_get', return_value=(200, {"display_name": "User"})):
            result = conn.test_connection()
            assert result["ok"] is True


# ==================================================================
# Integration Service (with mocked DB)
# ==================================================================

class TestIntegrationService:
    @pytest.fixture
    def db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, db):
        svc = IntegrationService.__new__(IntegrationService)
        svc.db = db
        svc.repo = MagicMock(spec=IntegrationRepository)
        return svc

    def test_connect_unknown_type(self, service):
        result = service.connect(user_id=1, integration_type="nonexistent", name="test")
        assert result["status"] == "error"

    def test_connect_success(self, service):
        integration = MagicMock(spec=Integration)
        integration.id = 1
        integration.status = "active"
        service.repo.create.return_value = integration

        with patch('app.integrations.service.ConnectorRegistry') as mock_reg:
            mock_connector = MagicMock()
            mock_connector.test_connection.return_value = {"ok": True, "message": "Connected"}
            mock_reg.get.return_value = MagicMock
            mock_reg.create.return_value = mock_connector
            result = service.connect(user_id=1, integration_type="jira", name="My Jira")
            assert result["id"] == 1

    def test_list_integrations(self, service):
        i = MagicMock(spec=Integration)
        i.id = 1
        i.integration_type = "jira"
        i.name = "Test"
        i.auth_method = "api_key"
        i.status = "active"
        i.base_url = None
        i.config = {}
        i.repository_id = None
        i.last_sync_at = None
        i.last_error = None
        i.sync_count = 5
        i.is_active = True
        i.created_at = None
        i.updated_at = None
        service.repo.get_by_user.return_value = [i]
        result = service.list_integrations(user_id=1)
        assert len(result) == 1
        assert result[0]["name"] == "Test"

    def test_sync_not_found(self, service):
        service.repo.get_by_id.return_value = None
        result = service.sync(999)
        assert result["status"] == "error"

    def test_disconnect(self, service):
        integration = MagicMock(spec=Integration)
        integration.id = 1
        service.repo.get_by_id.return_value = integration
        result = service.disconnect(1)
        assert result["status"] == "success"
        service.repo.deactivate.assert_called_once()


# ==================================================================
# Models
# ==================================================================

class TestModels:
    def test_integration_types(self):
        assert IntegrationType.JIRA == "jira"
        assert IntegrationType.SLACK == "slack"
        assert IntegrationType.TEAMS == "teams"
        assert IntegrationType.CONFLUENCE == "confluence"
        assert IntegrationType.SERVICENOW == "servicenow"
        assert IntegrationType.GITLAB == "gitlab"
        assert IntegrationType.BITBUCKET == "bitbucket"
        assert IntegrationType.AZURE_DEVOPS == "azure_devops"

    def test_auth_methods(self):
        assert AuthMethod.OAUTH2 == "oauth2"
        assert AuthMethod.API_KEY == "api_key"
        assert AuthMethod.PAT == "personal_access_token"

    def test_statuses(self):
        assert IntegrationStatus.ACTIVE == "active"
        assert IntegrationStatus.ERROR == "error"
        assert IntegrationStatus.DISCONNECTED == "disconnected"

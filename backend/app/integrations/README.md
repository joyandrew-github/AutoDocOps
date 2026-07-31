# Enterprise Integrations Platform

Connector-based integration framework for AutoDocOps, supporting 8 enterprise services.

## Architecture

```
integrations/
├── base.py           — BaseConnector, RateLimiter, RetryPolicy
├── registry.py       — ConnectorRegistry (auto-discovery)
├── service.py        — IntegrationService (orchestration)
├── repository.py     — IntegrationRepository (DB layer)
└── connectors/
    ├── jira.py        — Issue linking, PR linking, AI summaries
    ├── azure_devops.py — Repo sync, pipeline triggers, build status
    ├── gitlab.py      — Repo sync, pipeline triggers, build status
    ├── bitbucket.py   — Repo sync, pipeline triggers, build status
    ├── slack.py       — Notifications (AI, pipeline, risk, PR)
    ├── teams.py       — Adaptive Card notifications
    ├── confluence.py  — Publish docs, architecture, change reports
    └── servicenow.py  — Incidents, change requests, CMDB
```

## Supported Integrations

| Connector | Auth Methods | Key Actions |
|-----------|-------------|-------------|
| **Jira** | API Key, OAuth2, Basic | Issue CRUD, PR linking, AI summaries |
| **Azure DevOps** | PAT, OAuth2 | Repo sync, pipeline trigger, build status |
| **GitLab** | PAT, OAuth2, API Key | Repo sync, pipeline trigger, build status |
| **Bitbucket** | Basic, OAuth2, API Key | Repo sync, pipeline trigger, build status |
| **Slack** | Bot Token, OAuth2, Webhook | AI/pipeline/risk/PR notifications |
| **Microsoft Teams** | Webhook, OAuth2 | Adaptive Card notifications |
| **Confluence** | API Key, OAuth2, Basic | Publish docs/architecture/reports |
| **ServiceNow** | Basic, OAuth2, API Key | Incidents, change requests, CMDB |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/integrations/connect` | Connect a new integration |
| `GET` | `/api/v1/integrations` | List all integrations |
| `GET` | `/api/v1/integrations/connectors` | List available connector types |
| `POST` | `/api/v1/integrations/sync` | Execute a sync action |
| `GET` | `/api/v1/integrations/{id}/status` | Get integration health |
| `GET` | `/api/v1/integrations/{id}/logs` | Get activity logs |
| `POST` | `/api/v1/integrations/{id}/disconnect` | Disconnect integration |

## Framework Features

- **BaseConnector** — Abstract base with HTTP helpers, headers, auth
- **ConnectorRegistry** — Decorator-based auto-registration
- **OAuth2 & API Key** — Multiple auth method support per connector
- **RetryPolicy** — Exponential backoff with configurable retries
- **RateLimiter** — Sliding-window in-memory rate limiting
- **IntegrationRepository** — Full CRUD + audit logging
- **IntegrationService** — Connect/sync/status/disconnect lifecycle

## Adding a New Connector

```python
from app.integrations.base import BaseConnector
from app.integrations.registry import ConnectorRegistry

@ConnectorRegistry.register
class MyConnector(BaseConnector):
    connector_type = "my_service"
    display_name = "My Service"
    supported_auth_methods = ["api_key"]
    supported_actions = ["test", "sync"]

    def test_connection(self):
        status, data = self._get("/api/health")
        return {"ok": status == 200, "message": str(data)}

    def sync(self, payload):
        # Implementation
        return {"status": "success"}
```

Then import in `connectors/__init__.py` and it's automatically available.

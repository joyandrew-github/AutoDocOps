"""Connector implementations — auto-register all connectors on import."""
from app.integrations.connectors.jira import JiraConnector
from app.integrations.connectors.azure_devops import AzureDevOpsConnector
from app.integrations.connectors.gitlab import GitLabConnector
from app.integrations.connectors.bitbucket import BitbucketConnector
from app.integrations.connectors.slack import SlackConnector
from app.integrations.connectors.teams import TeamsConnector
from app.integrations.connectors.confluence import ConfluenceConnector
from app.integrations.connectors.servicenow import ServiceNowConnector

__all__ = [
    "JiraConnector",
    "AzureDevOpsConnector",
    "GitLabConnector",
    "BitbucketConnector",
    "SlackConnector",
    "TeamsConnector",
    "ConfluenceConnector",
    "ServiceNowConnector",
]

"""ConnectorRegistry — discovers and instantiates connectors by type."""
from __future__ import annotations
from typing import Any, Type
from app.integrations.base import BaseConnector
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectorRegistry:
    """Global registry of available connector types."""

    _connectors: dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, connector_cls: Type[BaseConnector]) -> Type[BaseConnector]:
        """Register a connector class. Can be used as a decorator."""
        key = connector_cls.connector_type
        if not key:
            raise ValueError(f"Connector class {connector_cls.__name__} has no connector_type")
        cls._connectors[key] = connector_cls
        logger.debug(f"Registered connector: {key} -> {connector_cls.__name__}")
        return connector_cls

    @classmethod
    def get(cls, connector_type: str) -> Type[BaseConnector]:
        """Get a connector class by type."""
        if connector_type not in cls._connectors:
            raise ValueError(f"Unknown connector type: {connector_type}. Available: {list(cls._connectors.keys())}")
        return cls._connectors[connector_type]

    @classmethod
    def create(cls, connector_type: str, **kwargs: Any) -> BaseConnector:
        """Instantiate a connector by type."""
        connector_cls = cls.get(connector_type)
        return connector_cls(**kwargs)

    @classmethod
    def available(cls) -> list[dict[str, Any]]:
        """List all registered connector types with capabilities."""
        result = []
        for key, connector_cls in sorted(cls._connectors.items()):
            instance = connector_cls()
            result.append(instance.get_capabilities())
        return result

    @classmethod
    def types(cls) -> list[str]:
        """List registered connector type keys."""
        return sorted(cls._connectors.keys())

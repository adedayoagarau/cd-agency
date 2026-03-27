"""Connector framework — integrate external content sources with CD Agency."""

from __future__ import annotations

from runtime.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ContentItem,
    ContentType,
    HealthCheck,
    SyncMode,
    SyncResult,
)
from runtime.connectors.config import ConnectorConfigLoader
from runtime.connectors.exceptions import (
    ConnectorAuthError,
    ConnectorConfigError,
    ConnectorError,
    ConnectorNotFoundError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
)

__all__ = [
    # Base types
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorStatus",
    "ContentItem",
    "ContentType",
    "HealthCheck",
    "SyncMode",
    "SyncResult",
    # Config loader
    "ConnectorConfigLoader",
    # Exceptions
    "ConnectorAuthError",
    "ConnectorConfigError",
    "ConnectorError",
    "ConnectorNotFoundError",
    "ConnectorRateLimitError",
    "ConnectorTimeoutError",
]

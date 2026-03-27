"""Connector-specific exception hierarchy."""

from __future__ import annotations


class ConnectorError(Exception):
    """Base exception for all connector errors."""

    def __init__(self, message: str, connector_name: str | None = None) -> None:
        self.connector_name = connector_name
        super().__init__(message)


class ConnectorAuthError(ConnectorError):
    """Raised when authentication with a connector fails."""


class ConnectorNotFoundError(ConnectorError):
    """Raised when a requested resource is not found in the connector."""


class ConnectorConfigError(ConnectorError):
    """Raised when connector configuration is invalid or missing."""


class ConnectorRateLimitError(ConnectorError):
    """Raised when a connector's rate limit has been exceeded."""


class ConnectorTimeoutError(ConnectorError):
    """Raised when a connector request times out."""

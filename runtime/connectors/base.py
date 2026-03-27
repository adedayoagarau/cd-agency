"""Core connector types and abstract base class for all connectors."""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from runtime.connectors.exceptions import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ConnectorStatus(str, Enum):
    """Health status of a connector."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNAUTHORIZED = "unauthorized"
    RATE_LIMITED = "rate_limited"


class SyncMode(str, Enum):
    """Direction of data synchronisation."""

    PULL = "pull"
    PUSH = "push"
    BIDIRECTIONAL = "bidirectional"


class ContentType(str, Enum):
    """Recognised content types across connectors."""

    ARTICLE = "article"
    PAGE = "page"
    COMPONENT = "component"
    DESIGN = "design"
    DATABASE = "database"
    FILE = "file"
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ConnectorConfig:
    """Configuration for a single connector instance."""

    name: str
    type: str
    base_url: str | None = None
    credentials: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    sync_mode: SyncMode = SyncMode.PULL
    rate_limit: int | None = None  # requests per minute
    pool_size: int = 10
    cache_ttl: int = 300  # seconds
    timeout: int = 30  # seconds
    enabled: bool = True


@dataclass
class ContentItem:
    """A single piece of content retrieved from or sent to a connector."""

    id: str
    title: str | None = None
    content: str | None = None
    content_type: ContentType | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    url: str | None = None
    tags: list[str] = field(default_factory=list)
    author: str | None = None
    status: str | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)
    connector_id: str | None = None


@dataclass
class HealthCheck:
    """Result of a connector health check."""

    status: ConnectorStatus
    message: str
    latency_ms: float | None = None
    last_sync: datetime | None = None
    error: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncResult:
    """Summary of a synchronisation run."""

    success: bool
    items_processed: int
    items_created: int
    items_updated: int
    items_failed: int
    errors: list[str] = field(default_factory=list)
    duration_ms: float = 0.0


# ---------------------------------------------------------------------------
# Abstract base connector
# ---------------------------------------------------------------------------

class BaseConnector(ABC):
    """Abstract base class that every concrete connector must implement."""

    CONNECTOR_TYPE: str = "base"
    SUPPORTED_CONTENT_TYPES: list[ContentType] = []

    def __init__(self, config: ConnectorConfig) -> None:
        self.config = config
        self.name = config.name
        self.type = config.type
        self._authenticated: bool = False
        self._cache: dict[str, Any] = {}

    # -- context manager (synchronous) ------------------------------------

    def __enter__(self) -> BaseConnector:
        self.authenticate()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()

    # -- abstract interface ------------------------------------------------

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the external service."""
        ...

    @abstractmethod
    def health_check(self) -> HealthCheck:
        """Return current health status of the connector."""
        ...

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Return a JSON-style schema describing available fields."""
        ...

    @abstractmethod
    def list_content(
        self,
        content_type: ContentType | None = None,
        limit: int = 50,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[ContentItem]:
        """List content items, optionally filtered."""
        ...

    @abstractmethod
    def get_content(self, content_id: str) -> ContentItem | None:
        """Retrieve a single content item by ID."""
        ...

    @abstractmethod
    def create_content(self, item: ContentItem) -> ContentItem:
        """Create a new content item and return it."""
        ...

    @abstractmethod
    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        """Update an existing content item and return the updated version."""
        ...

    @abstractmethod
    def delete_content(self, content_id: str) -> bool:
        """Delete a content item. Return True on success."""
        ...

    # -- concrete helpers --------------------------------------------------

    def get_supported_content_types(self) -> list[ContentType]:
        """Return the content types this connector can handle."""
        return list(self.SUPPORTED_CONTENT_TYPES)

    def validate_config(self) -> bool:
        """Validate that the connector configuration is minimally correct."""
        if not self.config.name:
            return False
        if not self.config.type:
            return False
        return True

    def close(self) -> None:
        """Release any held resources."""
        self._cache.clear()
        self._authenticated = False

    # -- HTTP helper using urllib ------------------------------------------

    def _get_default_headers(self) -> dict[str, str]:
        """Return default HTTP headers for outgoing requests."""
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        token = self.config.credentials.get("token") or self.config.credentials.get(
            "api_key"
        )
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _make_request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Perform a synchronous HTTP request via :mod:`urllib.request`.

        Returns the parsed JSON body as a dict.
        """
        merged_headers = self._get_default_headers()
        if headers:
            merged_headers.update(headers)

        body: bytes | None = None
        if data is not None:
            body = json.dumps(data).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=body,
            headers=merged_headers,
            method=method.upper(),
        )

        effective_timeout = timeout or self.config.timeout

        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=effective_timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            elapsed = (time.monotonic() - start) * 1000
            if exc.code == 401:
                raise ConnectorAuthError(
                    f"Authentication failed ({exc.code})",
                    connector_name=self.name,
                ) from exc
            if exc.code == 429:
                raise ConnectorRateLimitError(
                    f"Rate limited ({exc.code})",
                    connector_name=self.name,
                ) from exc
            raise ConnectorError(
                f"HTTP {exc.code}: {exc.reason} ({elapsed:.0f}ms)",
                connector_name=self.name,
            ) from exc
        except urllib.error.URLError as exc:
            if "timed out" in str(exc.reason):
                raise ConnectorTimeoutError(
                    f"Request timed out after {effective_timeout}s",
                    connector_name=self.name,
                ) from exc
            raise ConnectorError(
                str(exc.reason),
                connector_name=self.name,
            ) from exc

    # -- brand signal extraction -------------------------------------------

    def _extract_brand_signals(self, content: str) -> dict[str, Any]:
        """Run basic tone / voice / terminology analysis on *content*.

        Returns a dict with keys ``tone``, ``voice``, ``terminology``.
        """
        signals: dict[str, Any] = {
            "tone": [],
            "voice": "unknown",
            "terminology": [],
        }

        if not content:
            return signals

        lower = content.lower()

        # Tone indicators
        tone_markers = {
            "formal": [
                "therefore", "consequently", "furthermore", "regarding",
                "hereby", "pursuant",
            ],
            "casual": [
                "hey", "cool", "awesome", "gonna", "wanna", "btw",
            ],
            "friendly": [
                "we're happy", "glad to", "welcome", "thanks", "thank you",
            ],
            "urgent": [
                "immediately", "critical", "asap", "urgent", "action required",
            ],
        }

        for tone, markers in tone_markers.items():
            if any(m in lower for m in markers):
                signals["tone"].append(tone)

        # Voice — simple active/passive heuristic
        passive_patterns = [
            r"\b(?:is|are|was|were|been|being)\s+\w+ed\b",
        ]
        passive_count = sum(
            len(re.findall(p, lower)) for p in passive_patterns
        )
        word_count = len(content.split())
        if word_count > 0 and passive_count / max(word_count, 1) > 0.1:
            signals["voice"] = "passive"
        else:
            signals["voice"] = "active"

        # Terminology — extract capitalised multi-word terms
        term_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"
        terms = re.findall(term_pattern, content)
        signals["terminology"] = list(dict.fromkeys(terms))[:20]

        return signals

"""Tests for connector base types and BaseConnector."""

from __future__ import annotations

from typing import Any

import pytest

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
from runtime.connectors.exceptions import (
    ConnectorAuthError,
    ConnectorConfigError,
    ConnectorError,
    ConnectorNotFoundError,
    ConnectorRateLimitError,
    ConnectorTimeoutError,
)


# ---------------------------------------------------------------------------
# Helper — concrete mock connector
# ---------------------------------------------------------------------------


class MockConnector(BaseConnector):
    CONNECTOR_TYPE = "mock"
    SUPPORTED_CONTENT_TYPES = [ContentType.ARTICLE, ContentType.PAGE]

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self._items: list[ContentItem] = []

    def authenticate(self) -> bool:
        self._authenticated = True
        return True

    def health_check(self) -> HealthCheck:
        return HealthCheck(status=ConnectorStatus.HEALTHY, message="OK", latency_ms=1.0)

    def get_schema(self) -> dict[str, Any]:
        return {"mock": True}

    def list_content(
        self,
        content_type: ContentType | None = None,
        limit: int = 50,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[ContentItem]:
        items = self._items
        if content_type:
            items = [i for i in items if i.content_type == content_type]
        return items[offset : offset + limit]

    def get_content(self, content_id: str) -> ContentItem | None:
        for item in self._items:
            if item.id == content_id:
                return item
        return None

    def create_content(self, item: ContentItem) -> ContentItem:
        self._items.append(item)
        return item

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        for i, existing in enumerate(self._items):
            if existing.id == content_id:
                self._items[i] = item
                return item
        raise ConnectorNotFoundError(f"Not found: {content_id}")

    def delete_content(self, content_id: str) -> bool:
        for i, existing in enumerate(self._items):
            if existing.id == content_id:
                self._items.pop(i)
                return True
        return False


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TestEnums:
    def test_connector_status_values(self):
        assert ConnectorStatus.HEALTHY.value == "healthy"
        assert ConnectorStatus.RATE_LIMITED.value == "rate_limited"

    def test_sync_mode_values(self):
        assert SyncMode.PULL.value == "pull"
        assert SyncMode.BIDIRECTIONAL.value == "bidirectional"

    def test_content_type_values(self):
        assert ContentType.ARTICLE.value == "article"
        assert ContentType.DESIGN.value == "design"
        assert ContentType.DATABASE.value == "database"


# ---------------------------------------------------------------------------
# ConnectorConfig
# ---------------------------------------------------------------------------


class TestConnectorConfig:
    def test_defaults(self):
        cfg = ConnectorConfig(name="test", type="mock")
        assert cfg.name == "test"
        assert cfg.type == "mock"
        assert cfg.base_url is None
        assert cfg.credentials == {}
        assert cfg.settings == {}
        assert cfg.sync_mode == SyncMode.PULL
        assert cfg.rate_limit is None
        assert cfg.pool_size == 10
        assert cfg.cache_ttl == 300
        assert cfg.timeout == 30
        assert cfg.enabled is True

    def test_custom_values(self):
        cfg = ConnectorConfig(
            name="prod",
            type="contentful",
            base_url="https://api.example.com",
            credentials={"key": "secret"},
            sync_mode=SyncMode.BIDIRECTIONAL,
            rate_limit=100,
            enabled=False,
        )
        assert cfg.base_url == "https://api.example.com"
        assert cfg.credentials["key"] == "secret"
        assert cfg.sync_mode == SyncMode.BIDIRECTIONAL
        assert cfg.rate_limit == 100
        assert cfg.enabled is False


# ---------------------------------------------------------------------------
# ContentItem
# ---------------------------------------------------------------------------


class TestContentItem:
    def test_defaults(self):
        item = ContentItem(id="123")
        assert item.id == "123"
        assert item.title is None
        assert item.content is None
        assert item.content_type is None
        assert item.metadata == {}
        assert item.tags == []
        assert item.raw_data == {}

    def test_full_item(self):
        item = ContentItem(
            id="abc",
            title="Test Article",
            content="Hello world",
            content_type=ContentType.ARTICLE,
            tags=["test", "demo"],
            connector_id="my-connector",
        )
        assert item.title == "Test Article"
        assert item.content_type == ContentType.ARTICLE
        assert len(item.tags) == 2


# ---------------------------------------------------------------------------
# HealthCheck
# ---------------------------------------------------------------------------


class TestHealthCheck:
    def test_defaults(self):
        h = HealthCheck(status=ConnectorStatus.HEALTHY, message="OK")
        assert h.status == ConnectorStatus.HEALTHY
        assert h.latency_ms is None
        assert h.error is None

    def test_unhealthy(self):
        h = HealthCheck(
            status=ConnectorStatus.UNHEALTHY,
            message="Connection refused",
            error="ECONNREFUSED",
        )
        assert h.status == ConnectorStatus.UNHEALTHY
        assert h.error == "ECONNREFUSED"


# ---------------------------------------------------------------------------
# SyncResult
# ---------------------------------------------------------------------------


class TestSyncResult:
    def test_defaults(self):
        r = SyncResult(
            success=True, items_processed=10, items_created=8, items_updated=2, items_failed=0
        )
        assert r.success is True
        assert r.items_processed == 10
        assert r.errors == []

    def test_failed(self):
        r = SyncResult(
            success=False,
            items_processed=5,
            items_created=0,
            items_updated=0,
            items_failed=5,
            errors=["timeout"],
        )
        assert not r.success
        assert len(r.errors) == 1


# ---------------------------------------------------------------------------
# BaseConnector via MockConnector
# ---------------------------------------------------------------------------


class TestBaseConnector:
    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            name="test-mock",
            type="mock",
            credentials={"api_key": "test-key"},
        )

    @pytest.fixture
    def connector(self, config):
        return MockConnector(config)

    def test_init(self, connector):
        assert connector.name == "test-mock"
        assert connector.type == "mock"
        assert connector._authenticated is False

    def test_authenticate(self, connector):
        assert connector.authenticate() is True
        assert connector._authenticated is True

    def test_health_check(self, connector):
        h = connector.health_check()
        assert h.status == ConnectorStatus.HEALTHY

    def test_get_schema(self, connector):
        schema = connector.get_schema()
        assert schema == {"mock": True}

    def test_supported_content_types(self, connector):
        types = connector.get_supported_content_types()
        assert ContentType.ARTICLE in types
        assert ContentType.PAGE in types

    def test_validate_config(self, connector):
        assert connector.validate_config() is True

    def test_validate_config_empty_name(self):
        cfg = ConnectorConfig(name="", type="mock")
        conn = MockConnector(cfg)
        assert conn.validate_config() is False

    def test_validate_config_empty_type(self):
        cfg = ConnectorConfig(name="test", type="")
        conn = MockConnector(cfg)
        assert conn.validate_config() is False

    def test_list_content_empty(self, connector):
        items = connector.list_content()
        assert items == []

    def test_crud_operations(self, connector):
        item = ContentItem(id="1", title="Test", content="Hello", content_type=ContentType.ARTICLE)

        # Create
        created = connector.create_content(item)
        assert created.id == "1"

        # Read
        fetched = connector.get_content("1")
        assert fetched is not None
        assert fetched.title == "Test"

        # Read not found
        assert connector.get_content("999") is None

        # List
        items = connector.list_content()
        assert len(items) == 1

        # Update
        updated_item = ContentItem(id="1", title="Updated", content="World")
        connector.update_content("1", updated_item)
        fetched2 = connector.get_content("1")
        assert fetched2.title == "Updated"

        # Delete
        assert connector.delete_content("1") is True
        assert connector.get_content("1") is None
        assert connector.delete_content("1") is False

    def test_list_content_with_type_filter(self, connector):
        connector.create_content(
            ContentItem(id="1", content_type=ContentType.ARTICLE)
        )
        connector.create_content(
            ContentItem(id="2", content_type=ContentType.PAGE)
        )
        articles = connector.list_content(content_type=ContentType.ARTICLE)
        assert len(articles) == 1
        assert articles[0].id == "1"

    def test_list_content_with_limit_offset(self, connector):
        for i in range(5):
            connector.create_content(ContentItem(id=str(i)))
        items = connector.list_content(limit=2, offset=1)
        assert len(items) == 2
        assert items[0].id == "1"

    def test_context_manager(self, config):
        with MockConnector(config) as conn:
            assert conn._authenticated is True
        assert conn._authenticated is False

    def test_close_clears_cache(self, connector):
        connector._cache["key"] = "value"
        connector.close()
        assert connector._cache == {}

    def test_brand_signal_extraction(self, connector):
        signals = connector._extract_brand_signals(
            "This is a professional and formal article. Furthermore, we are glad to welcome you."
        )
        assert "formal" in signals["tone"]
        assert "friendly" in signals["tone"]
        assert signals["voice"] in ("active", "passive")
        assert isinstance(signals["terminology"], list)

    def test_brand_signal_extraction_empty(self, connector):
        signals = connector._extract_brand_signals("")
        assert signals["tone"] == []
        assert signals["voice"] == "unknown"

    def test_default_headers(self, connector):
        headers = connector._get_default_headers()
        assert "Content-Type" in headers
        assert "Accept" in headers
        # Should include Bearer token from credentials
        assert "Authorization" in headers
        assert "test-key" in headers["Authorization"]


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TestExceptions:
    def test_connector_error(self):
        err = ConnectorError("test error", connector_name="my-conn")
        assert str(err) == "test error"
        assert err.connector_name == "my-conn"

    def test_connector_error_hierarchy(self):
        assert issubclass(ConnectorAuthError, ConnectorError)
        assert issubclass(ConnectorNotFoundError, ConnectorError)
        assert issubclass(ConnectorConfigError, ConnectorError)
        assert issubclass(ConnectorRateLimitError, ConnectorError)
        assert issubclass(ConnectorTimeoutError, ConnectorError)

    def test_exception_instances(self):
        e1 = ConnectorAuthError("auth failed", connector_name="x")
        assert isinstance(e1, ConnectorError)
        assert isinstance(e1, Exception)

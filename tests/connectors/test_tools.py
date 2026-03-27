"""Tests for connector tools."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from runtime.connectors.base import (
    ConnectorConfig,
    ConnectorStatus,
    ContentItem,
    ContentType,
    HealthCheck,
)
from runtime.tools.base import ToolResult


# ---------------------------------------------------------------------------
# Helper — mock connector for tool tests
# ---------------------------------------------------------------------------

# All tools do `from runtime.connectors.registry import connector_registry`
# inside execute(), so we patch the singleton on the registry module.
_REGISTRY_PATCH = "runtime.connectors.registry.connector_registry"


def _make_mock_connector(items: list[ContentItem] | None = None):
    """Create a mock connector with pre-loaded items."""
    conn = MagicMock()
    conn.name = "test"
    conn.type = "mock"
    conn.config = ConnectorConfig(name="test", type="mock")
    conn.get_supported_content_types.return_value = [ContentType.ARTICLE]

    _items = items or []

    def _list_content(content_type=None, limit=50, **kwargs):
        result = _items
        if content_type:
            result = [i for i in result if i.content_type == content_type]
        return result[:limit]

    def _get_content(content_id):
        for i in _items:
            if i.id == content_id:
                return i
        return None

    conn.list_content.side_effect = _list_content
    conn.get_content.side_effect = _get_content
    conn.create_content.side_effect = lambda item: item
    conn.update_content.side_effect = lambda cid, item: item
    conn.health_check.return_value = HealthCheck(
        status=ConnectorStatus.HEALTHY, message="OK"
    )
    return conn


# ---------------------------------------------------------------------------
# FetchContentTool
# ---------------------------------------------------------------------------


class TestFetchContentTool:
    def test_fetch_by_id(self):
        from runtime.connectors.tools.fetch_content import FetchContentTool

        item = ContentItem(
            id="abc", title="Test", content="Hello", content_type=ContentType.ARTICLE
        )
        mock_conn = _make_mock_connector([item])

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = FetchContentTool()
            result = tool.execute(connector_name="test", content_id="abc")

        assert result.success is True
        assert result.data["total"] == 1
        assert result.data["content"][0]["id"] == "abc"

    def test_fetch_not_found(self):
        from runtime.connectors.tools.fetch_content import FetchContentTool

        mock_conn = _make_mock_connector([])

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = FetchContentTool()
            result = tool.execute(connector_name="test", content_id="missing")

        assert result.success is False
        assert "not found" in result.error

    def test_fetch_list(self):
        from runtime.connectors.tools.fetch_content import FetchContentTool

        items = [
            ContentItem(id="1", title="A", content_type=ContentType.ARTICLE),
            ContentItem(id="2", title="B", content_type=ContentType.PAGE),
        ]
        mock_conn = _make_mock_connector(items)

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = FetchContentTool()
            result = tool.execute(connector_name="test")

        assert result.success is True
        assert result.data["total"] == 2

    def test_fetch_connector_not_found(self):
        from runtime.connectors.tools.fetch_content import FetchContentTool

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = None
            tool = FetchContentTool()
            result = tool.execute(connector_name="missing")

        assert result.success is False
        assert "not found" in result.error

    def test_tool_schema(self):
        from runtime.connectors.tools.fetch_content import FetchContentTool

        tool = FetchContentTool()
        schema = tool.to_llm_tool_schema()
        assert schema["name"] == "fetch_content"
        assert "connector_name" in schema["input_schema"]["properties"]


# ---------------------------------------------------------------------------
# PushContentTool
# ---------------------------------------------------------------------------


class TestPushContentTool:
    def test_push_create(self):
        from runtime.connectors.tools.push_content import PushContentTool

        mock_conn = _make_mock_connector()

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = PushContentTool()
            result = tool.execute(
                connector_name="test",
                title="New Article",
                content="Body text",
            )

        assert result.success is True
        assert result.data["action"] == "created"

    def test_push_update(self):
        from runtime.connectors.tools.push_content import PushContentTool

        mock_conn = _make_mock_connector()

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = PushContentTool()
            result = tool.execute(
                connector_name="test",
                content_id="existing-id",
                title="Updated",
                content="New body",
            )

        assert result.success is True
        assert result.data["action"] == "updated"

    def test_push_connector_not_found(self):
        from runtime.connectors.tools.push_content import PushContentTool

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = None
            tool = PushContentTool()
            result = tool.execute(connector_name="nope", title="X", content="Y")

        assert result.success is False


# ---------------------------------------------------------------------------
# SyncContentTool
# ---------------------------------------------------------------------------


class TestSyncContentTool:
    def test_sync_pull(self):
        from runtime.connectors.tools.sync_content import SyncContentTool

        items = [ContentItem(id="1"), ContentItem(id="2")]
        mock_conn = _make_mock_connector(items)

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = SyncContentTool()
            result = tool.execute(connector_name="test", direction="pull")

        assert result.success is True

    def test_sync_dry_run(self):
        from runtime.connectors.tools.sync_content import SyncContentTool

        mock_conn = _make_mock_connector([ContentItem(id="1")])

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = SyncContentTool()
            result = tool.execute(
                connector_name="test", direction="pull", dry_run=True
            )

        assert result.success is True

    def test_sync_connector_not_found(self):
        from runtime.connectors.tools.sync_content import SyncContentTool

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = None
            tool = SyncContentTool()
            result = tool.execute(connector_name="nope")

        assert result.success is False


# ---------------------------------------------------------------------------
# ListSourcesTool
# ---------------------------------------------------------------------------


class TestListSourcesTool:
    def test_list_specific(self):
        from runtime.connectors.tools.list_sources import ListSourcesTool

        mock_conn = _make_mock_connector()

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = mock_conn
            tool = ListSourcesTool()
            result = tool.execute(connector_name="test")

        assert result.success is True
        assert "test" in result.data["sources"]

    def test_list_all(self):
        from runtime.connectors.tools.list_sources import ListSourcesTool

        mock_conn = _make_mock_connector()

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.list_enabled.return_value = ["a"]
            mock_reg.get_connector.return_value = mock_conn
            tool = ListSourcesTool()
            result = tool.execute()

        assert result.success is True
        assert result.data["total"] >= 1

    def test_list_connector_not_found(self):
        from runtime.connectors.tools.list_sources import ListSourcesTool

        with patch(_REGISTRY_PATCH) as mock_reg:
            mock_reg.get_connector.return_value = None
            tool = ListSourcesTool()
            result = tool.execute(connector_name="nope")

        assert result.success is False

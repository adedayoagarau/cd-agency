"""Tests for ConnectorRegistry."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from runtime.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ContentItem,
    ContentType,
    HealthCheck,
    SyncMode,
)
from runtime.connectors.registry import ConnectorRegistry


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


class StubConnector(BaseConnector):
    CONNECTOR_TYPE = "stub"
    SUPPORTED_CONTENT_TYPES = [ContentType.ARTICLE]

    def authenticate(self) -> bool:
        return True

    def health_check(self) -> HealthCheck:
        return HealthCheck(status=ConnectorStatus.HEALTHY, message="stub OK")

    def get_schema(self) -> dict[str, Any]:
        return {}

    def list_content(self, **kwargs) -> list[ContentItem]:
        return []

    def get_content(self, content_id: str) -> ContentItem | None:
        return None

    def create_content(self, item: ContentItem) -> ContentItem:
        return item

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        return item

    def delete_content(self, content_id: str) -> bool:
        return True


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestConnectorRegistry:
    @pytest.fixture
    def registry(self):
        return ConnectorRegistry()

    def test_fresh_registry(self, registry):
        assert registry._initialized is False
        assert registry._connector_classes == {}
        assert registry._connector_configs == {}

    def test_register_connector_class(self, registry):
        registry.register_connector_class("stub", StubConnector)
        assert "stub" in registry._connector_classes

    def test_register_invalid_class(self, registry):
        with pytest.raises(TypeError):
            registry.register_connector_class("bad", dict)  # type: ignore[arg-type]

    def test_add_and_get_connector(self, registry):
        registry.register_connector_class("stub", StubConnector)
        cfg = ConnectorConfig(name="my-stub", type="stub")
        registry.add_config("my-stub", cfg)
        registry._initialized = True

        conn = registry.get_connector("my-stub")
        assert conn is not None
        assert isinstance(conn, StubConnector)
        assert conn.name == "my-stub"

    def test_get_connector_cached(self, registry):
        registry.register_connector_class("stub", StubConnector)
        cfg = ConnectorConfig(name="c", type="stub")
        registry.add_config("c", cfg)
        registry._initialized = True

        c1 = registry.get_connector("c")
        c2 = registry.get_connector("c")
        assert c1 is c2  # same instance

    def test_get_connector_not_configured(self, registry):
        registry._initialized = True
        assert registry.get_connector("unknown") is None

    def test_get_connector_disabled(self, registry):
        registry.register_connector_class("stub", StubConnector)
        cfg = ConnectorConfig(name="off", type="stub", enabled=False)
        registry.add_config("off", cfg)
        registry._initialized = True

        assert registry.get_connector("off") is None

    def test_get_connector_unknown_type(self, registry):
        cfg = ConnectorConfig(name="x", type="nonexistent")
        registry.add_config("x", cfg)
        registry._initialized = True

        assert registry.get_connector("x") is None

    def test_list_available_types(self, registry):
        registry.register_connector_class("stub", StubConnector)
        registry._initialized = True
        assert "stub" in registry.list_available_types()

    def test_list_configured(self, registry):
        cfg = ConnectorConfig(name="a", type="stub")
        registry.add_config("a", cfg)
        registry._initialized = True
        assert "a" in registry.list_configured()

    def test_list_enabled(self, registry):
        registry.add_config("on", ConnectorConfig(name="on", type="stub", enabled=True))
        registry.add_config("off", ConnectorConfig(name="off", type="stub", enabled=False))
        registry._initialized = True

        enabled = registry.list_enabled()
        assert "on" in enabled
        assert "off" not in enabled

    def test_remove_config(self, registry):
        registry.register_connector_class("stub", StubConnector)
        registry.add_config("rm", ConnectorConfig(name="rm", type="stub"))
        registry._initialized = True
        registry.get_connector("rm")  # populate instance cache

        registry.remove_config("rm")
        assert "rm" not in registry._connector_configs
        assert "rm" not in registry._connector_instances

    def test_close_all(self, registry):
        registry.register_connector_class("stub", StubConnector)
        registry.add_config("c1", ConnectorConfig(name="c1", type="stub"))
        registry.add_config("c2", ConnectorConfig(name="c2", type="stub"))
        registry._initialized = True
        registry.get_connector("c1")
        registry.get_connector("c2")

        registry.close_all()
        assert registry._connector_instances == {}

    def test_health_check_all(self, registry):
        registry.register_connector_class("stub", StubConnector)
        registry.add_config("h1", ConnectorConfig(name="h1", type="stub"))
        registry._initialized = True

        results = registry.health_check_all()
        assert "h1" in results
        assert results["h1"].status == ConnectorStatus.HEALTHY

    def test_load_configs_from_yaml(self, tmp_path):
        config_data = {
            "connectors": {
                "test-conn": {
                    "type": "stub",
                    "base_url": "https://example.com",
                    "credentials": {"key": "val"},
                    "settings": {"locale": "en"},
                    "sync_mode": "pull",
                    "rate_limit": 100,
                    "enabled": True,
                }
            }
        }
        config_file = tmp_path / "connectors.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        registry = ConnectorRegistry()
        registry.load_configs(str(config_file))

        assert "test-conn" in registry._connector_configs
        cfg = registry._connector_configs["test-conn"]
        assert cfg.type == "stub"
        assert cfg.base_url == "https://example.com"
        assert cfg.credentials == {"key": "val"}
        assert cfg.rate_limit == 100

    def test_load_configs_env_substitution(self, tmp_path):
        config_data = {
            "connectors": {
                "env-conn": {
                    "type": "stub",
                    "credentials": {
                        "token": "${TEST_CONN_TOKEN}",
                        "env_with_default": "${MISSING_VAR:fallback}",
                    },
                }
            }
        }
        config_file = tmp_path / "connectors.yaml"
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")

        with patch.dict(os.environ, {"TEST_CONN_TOKEN": "my-secret"}, clear=False):
            registry = ConnectorRegistry()
            registry.load_configs(str(config_file))

        cfg = registry._connector_configs["env-conn"]
        assert cfg.credentials["token"] == "my-secret"
        assert cfg.credentials["env_with_default"] == "fallback"

    def test_load_configs_missing_file(self):
        registry = ConnectorRegistry()
        registry.load_configs("/nonexistent/path.yaml")
        assert registry._connector_configs == {}

    def test_auto_discover_finds_providers(self):
        registry = ConnectorRegistry()
        registry._auto_discover_connectors()
        # Should find at least contentful, figma, notion, and stubs
        types = list(registry._connector_classes.keys())
        assert len(types) >= 3

    def test_initialize_idempotent(self):
        registry = ConnectorRegistry()
        registry.initialize()
        count1 = len(registry._connector_classes)
        registry.initialize()  # second call should be no-op
        assert len(registry._connector_classes) == count1

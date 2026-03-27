"""Tests for connector config loader."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest
import yaml

from runtime.connectors.base import ConnectorConfig, SyncMode
from runtime.connectors.config import ConnectorConfigLoader


class TestConnectorConfigLoader:
    def test_load_from_file(self, tmp_path):
        data = {
            "connectors": {
                "test": {
                    "type": "contentful",
                    "base_url": "https://cdn.contentful.com",
                    "credentials": {"space_id": "sp", "access_token": "tok"},
                    "settings": {"locale": "en-US"},
                    "sync_mode": "pull",
                    "rate_limit": 200,
                    "pool_size": 5,
                    "cache_ttl": 600,
                    "timeout": 15,
                    "enabled": True,
                }
            }
        }
        path = tmp_path / "connectors.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        configs = ConnectorConfigLoader.load_from_file(str(path))
        assert "test" in configs
        cfg = configs["test"]
        assert isinstance(cfg, ConnectorConfig)
        assert cfg.type == "contentful"
        assert cfg.base_url == "https://cdn.contentful.com"
        assert cfg.credentials["space_id"] == "sp"
        assert cfg.sync_mode == SyncMode.PULL
        assert cfg.rate_limit == 200
        assert cfg.pool_size == 5
        assert cfg.cache_ttl == 600
        assert cfg.timeout == 15

    def test_load_missing_file(self):
        from runtime.connectors.exceptions import ConnectorConfigError

        with pytest.raises(ConnectorConfigError):
            ConnectorConfigLoader.load_from_file("/nonexistent.yaml")

    def test_env_var_substitution(self, tmp_path):
        data = {
            "connectors": {
                "env-test": {
                    "type": "notion",
                    "credentials": {
                        "api_key": "${TEST_NOTION_KEY}",
                        "with_default": "${MISSING_KEY:default_val}",
                    },
                }
            }
        }
        path = tmp_path / "connectors.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        with patch.dict(os.environ, {"TEST_NOTION_KEY": "real-key"}, clear=False):
            configs = ConnectorConfigLoader.load_from_file(str(path))

        cfg = configs["env-test"]
        assert cfg.credentials["api_key"] == "real-key"
        assert cfg.credentials["with_default"] == "default_val"

    def test_multiple_connectors(self, tmp_path):
        data = {
            "connectors": {
                "a": {"type": "contentful"},
                "b": {"type": "notion", "enabled": False},
                "c": {"type": "figma", "sync_mode": "pull"},
            }
        }
        path = tmp_path / "connectors.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        configs = ConnectorConfigLoader.load_from_file(str(path))
        assert len(configs) == 3
        assert configs["b"].enabled is False
        assert configs["c"].sync_mode == SyncMode.PULL

    def test_defaults_applied(self, tmp_path):
        data = {"connectors": {"minimal": {"type": "sanity"}}}
        path = tmp_path / "connectors.yaml"
        path.write_text(yaml.dump(data), encoding="utf-8")

        configs = ConnectorConfigLoader.load_from_file(str(path))
        cfg = configs["minimal"]
        assert cfg.base_url is None
        assert cfg.credentials == {}
        assert cfg.settings == {}
        assert cfg.sync_mode == SyncMode.PULL
        assert cfg.rate_limit is None
        assert cfg.pool_size == 10
        assert cfg.cache_ttl == 300
        assert cfg.timeout == 30
        assert cfg.enabled is True

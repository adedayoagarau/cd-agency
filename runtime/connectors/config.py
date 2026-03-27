"""Load and resolve connector configurations from YAML files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

from runtime.connectors.base import ConnectorConfig, SyncMode
from runtime.connectors.exceptions import ConnectorConfigError


class ConnectorConfigLoader:
    """Static helper for loading connector configs from YAML files."""

    @staticmethod
    def load_from_file(path: str | Path) -> dict[str, ConnectorConfig]:
        """Load connector configurations from a YAML file.

        The file should contain a top-level ``connectors`` mapping where each
        key is the connector name and its value holds the connector settings.

        Returns a dict keyed by connector name.
        """
        filepath = Path(path)
        if not filepath.exists():
            raise ConnectorConfigError(
                f"Config file not found: {filepath}",
            )

        try:
            raw = filepath.read_text(encoding="utf-8")
            data = yaml.safe_load(raw) or {}
        except yaml.YAMLError as exc:
            raise ConnectorConfigError(
                f"Invalid YAML in {filepath}: {exc}",
            ) from exc

        # Perform environment-variable substitution on the whole tree
        data = ConnectorConfigLoader._substitute_env_vars(data)

        connectors_data: dict[str, Any] = data.get("connectors", data)
        if not isinstance(connectors_data, dict):
            raise ConnectorConfigError(
                "Expected a mapping of connector names to config dicts.",
            )

        configs: dict[str, ConnectorConfig] = {}
        for name, cfg in connectors_data.items():
            if not isinstance(cfg, dict):
                continue
            configs[name] = ConnectorConfigLoader._create_config(name, cfg)

        return configs

    @staticmethod
    def _substitute_env_vars(data: Any) -> Any:
        """Recursively replace ``${VAR}`` and ``${VAR:default}`` placeholders.

        Walks dicts, lists, and strings.  Non-string leaves are returned
        unchanged.
        """
        if isinstance(data, dict):
            return {
                k: ConnectorConfigLoader._substitute_env_vars(v)
                for k, v in data.items()
            }
        if isinstance(data, list):
            return [ConnectorConfigLoader._substitute_env_vars(v) for v in data]
        if isinstance(data, str):
            pattern = re.compile(r"\$\{([^}]+)\}")

            def _replace(match: re.Match[str]) -> str:
                expr = match.group(1)
                if ":" in expr:
                    var, default = expr.split(":", 1)
                    return os.environ.get(var.strip(), default.strip())
                return os.environ.get(expr.strip(), match.group(0))

            return pattern.sub(_replace, data)
        return data

    @staticmethod
    def _create_config(name: str, data: dict[str, Any]) -> ConnectorConfig:
        """Build a :class:`ConnectorConfig` from a raw dict."""
        sync_mode_raw = data.get("sync_mode", "pull")
        try:
            sync_mode = SyncMode(sync_mode_raw)
        except ValueError:
            sync_mode = SyncMode.PULL

        return ConnectorConfig(
            name=name,
            type=data.get("type", "unknown"),
            base_url=data.get("base_url"),
            credentials=data.get("credentials", {}),
            settings=data.get("settings", {}),
            sync_mode=sync_mode,
            rate_limit=data.get("rate_limit"),
            pool_size=data.get("pool_size", 10),
            cache_ttl=data.get("cache_ttl", 300),
            timeout=data.get("timeout", 30),
            enabled=data.get("enabled", True),
        )

"""Registry for managing connectors with auto-discovery and lazy loading."""

from __future__ import annotations

import importlib
import inspect
import logging
import os
from pathlib import Path
from typing import Any, Type

import yaml

from runtime.connectors.base import BaseConnector, ConnectorConfig, HealthCheck, ConnectorStatus

_logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """Registry for managing connectors with auto-discovery and lazy loading."""

    def __init__(self) -> None:
        self._connector_classes: dict[str, Type[BaseConnector]] = {}
        self._connector_instances: dict[str, BaseConnector] = {}
        self._connector_configs: dict[str, ConnectorConfig] = {}
        self._initialized = False

    def initialize(self, config_path: str | None = None) -> None:
        """Initialize with auto-discovery and config loading."""
        if self._initialized:
            return
        self._auto_discover_connectors()
        if config_path:
            self.load_configs(config_path)
        else:
            for default in ("config/connectors.yaml", "connectors.yaml"):
                if Path(default).exists():
                    self.load_configs(default)
                    break
        self._initialized = True

    def _auto_discover_connectors(self) -> None:
        """Auto-discover connector classes in providers/ directory."""
        providers_dir = Path(__file__).parent / "providers"
        if not providers_dir.exists():
            return
        for file_path in providers_dir.glob("*.py"):
            if file_path.name.startswith("_"):
                continue
            module_name = f"runtime.connectors.providers.{file_path.stem}"
            try:
                module = importlib.import_module(module_name)
                for _name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj)
                            and issubclass(obj, BaseConnector)
                            and obj is not BaseConnector
                            and hasattr(obj, "CONNECTOR_TYPE")
                            and obj.CONNECTOR_TYPE != "base"):
                        self._connector_classes[obj.CONNECTOR_TYPE] = obj
            except ImportError:
                _logger.debug("Could not import %s", module_name)
            except Exception as exc:
                _logger.warning("Error discovering %s: %s", module_name, exc)

    def register_connector_class(self, connector_type: str, cls: Type[BaseConnector]) -> None:
        if not issubclass(cls, BaseConnector):
            raise TypeError("Must inherit from BaseConnector")
        self._connector_classes[connector_type] = cls

    def load_configs(self, config_path: str) -> None:
        """Load connector configs from YAML."""
        path = Path(config_path)
        if not path.exists():
            return
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for name, cdata in data.get("connectors", {}).items():
                cdata = self._substitute_env_vars(cdata)
                from runtime.connectors.base import SyncMode
                config = ConnectorConfig(
                    name=name,
                    type=cdata["type"],
                    base_url=cdata.get("base_url"),
                    credentials=cdata.get("credentials", {}),
                    settings=cdata.get("settings", {}),
                    sync_mode=SyncMode(cdata.get("sync_mode", "pull")),
                    rate_limit=cdata.get("rate_limit"),
                    pool_size=cdata.get("pool_size", 10),
                    cache_ttl=cdata.get("cache_ttl", 300),
                    timeout=cdata.get("timeout", 30),
                    enabled=cdata.get("enabled", True),
                )
                self._connector_configs[name] = config
        except Exception as exc:
            _logger.warning("Failed to load connector configs from %s: %s", config_path, exc)

    def _substitute_env_vars(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {k: self._substitute_env_vars(v) for k, v in data.items()}
        if isinstance(data, list):
            return [self._substitute_env_vars(i) for i in data]
        if isinstance(data, str) and data.startswith("${") and data.endswith("}"):
            inner = data[2:-1]
            if ":" in inner:
                var, default = inner.split(":", 1)
                return os.getenv(var, default)
            return os.getenv(inner, data)
        return data

    def get_connector(self, name: str) -> BaseConnector | None:
        """Get connector instance with lazy loading."""
        if not self._initialized:
            self.initialize()
        if name in self._connector_instances:
            return self._connector_instances[name]
        config = self._connector_configs.get(name)
        if not config or not config.enabled:
            return None
        cls = self._connector_classes.get(config.type)
        if cls is None:
            _logger.warning("No connector class for type %s", config.type)
            return None
        try:
            instance = cls(config)
            if not instance.validate_config():
                return None
            self._connector_instances[name] = instance
            return instance
        except Exception as exc:
            _logger.error("Failed to create connector %s: %s", name, exc)
            return None

    def list_available_types(self) -> list[str]:
        if not self._initialized:
            self.initialize()
        return list(self._connector_classes.keys())

    def list_configured(self) -> list[str]:
        if not self._initialized:
            self.initialize()
        return list(self._connector_configs.keys())

    def list_enabled(self) -> list[str]:
        if not self._initialized:
            self.initialize()
        return [n for n, c in self._connector_configs.items() if c.enabled]

    def add_config(self, name: str, config: ConnectorConfig) -> None:
        self._connector_configs[name] = config

    def remove_config(self, name: str) -> None:
        self._connector_configs.pop(name, None)
        inst = self._connector_instances.pop(name, None)
        if inst:
            inst.close()

    def health_check_all(self) -> dict[str, HealthCheck]:
        results = {}
        for name in self.list_enabled():
            conn = self.get_connector(name)
            if conn:
                try:
                    results[name] = conn.health_check()
                except Exception as exc:
                    results[name] = HealthCheck(status=ConnectorStatus.UNHEALTHY, message=str(exc), error=str(exc))
            else:
                results[name] = HealthCheck(status=ConnectorStatus.UNHEALTHY, message="Could not initialize")
        return results

    def close_all(self) -> None:
        for inst in self._connector_instances.values():
            try:
                inst.close()
            except Exception:
                pass
        self._connector_instances.clear()


# Module-level singleton
connector_registry = ConnectorRegistry()

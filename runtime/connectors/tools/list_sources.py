"""Tool for listing available connector sources."""
from __future__ import annotations

from typing import Any

from runtime.tools.base import Tool, ToolResult


class ListSourcesTool(Tool):
    """List available connector sources and their configuration."""

    name = "list_sources"
    description = "List available connector sources and their configuration"
    parameters = {
        "connector_name": {
            "type": "string",
            "description": "Name of a specific connector to inspect",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        from runtime.connectors.registry import connector_registry

        connector_name = kwargs.get("connector_name")

        try:
            if connector_name:
                connector = connector_registry.get_connector(connector_name)
                if not connector:
                    return ToolResult(
                        success=False,
                        error=f"Connector '{connector_name}' not found or disabled",
                    )
                return ToolResult(
                    success=True,
                    data={
                        "sources": {
                            connector_name: {
                                "type": connector.type,
                                "supported_content_types": [
                                    ct.value
                                    for ct in connector.get_supported_content_types()
                                ],
                                "config": {
                                    "base_url": connector.config.base_url,
                                    "sync_mode": connector.config.sync_mode.value,
                                    "rate_limit": connector.config.rate_limit,
                                    "timeout": connector.config.timeout,
                                    "enabled": connector.config.enabled,
                                },
                            },
                        },
                    },
                )

            # List all enabled connectors
            enabled = connector_registry.list_enabled()
            sources: dict[str, Any] = {}
            for name in enabled:
                conn = connector_registry.get_connector(name)
                if conn:
                    sources[name] = {
                        "type": conn.type,
                        "supported_content_types": [
                            ct.value
                            for ct in conn.get_supported_content_types()
                        ],
                        "status": "enabled",
                    }
                else:
                    sources[name] = {
                        "type": "unknown",
                        "supported_content_types": [],
                        "status": "unavailable",
                    }

            return ToolResult(
                success=True,
                data={"sources": sources, "total": len(sources)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

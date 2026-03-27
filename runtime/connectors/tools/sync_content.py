"""Tool for synchronising content between the local system and connectors."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from runtime.tools.base import Tool, ToolResult


class SyncContentTool(Tool):
    """Synchronise content with external platforms via connectors."""

    name = "sync_content"
    description = "Synchronise content with external platforms via connectors"
    parameters = {
        "connector_name": {
            "type": "string",
            "description": "Name of the connector to use",
        },
        "direction": {
            "type": "string",
            "description": "Sync direction: pull or push (default: pull)",
            "optional": True,
        },
        "since_hours": {
            "type": "integer",
            "description": "Only sync content updated within the last N hours",
            "optional": True,
        },
        "dry_run": {
            "type": "boolean",
            "description": "If true, report what would be synced without making changes",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        from runtime.connectors.registry import connector_registry

        connector_name = kwargs.get("connector_name", "")
        direction = kwargs.get("direction", "pull")
        since_hours = kwargs.get("since_hours")
        dry_run = kwargs.get("dry_run", False)

        connector = connector_registry.get_connector(connector_name)
        if not connector:
            return ToolResult(
                success=False,
                error=f"Connector '{connector_name}' not found or disabled",
            )

        try:
            if direction == "push":
                return ToolResult(
                    success=False,
                    error="Push sync is not yet implemented",
                )

            # Pull direction
            items = connector.list_content(limit=100)

            if since_hours is not None:
                cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=since_hours)
                items = [
                    i for i in items
                    if i.updated_at is not None and i.updated_at >= cutoff
                ]

            if dry_run:
                return ToolResult(
                    success=True,
                    data={
                        "dry_run": True,
                        "direction": direction,
                        "items_found": len(items),
                        "connector": connector_name,
                    },
                )

            return ToolResult(
                success=True,
                data={
                    "direction": direction,
                    "items_synced": len(items),
                    "connector": connector_name,
                    "items": [
                        {"id": i.id, "title": i.title} for i in items
                    ],
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

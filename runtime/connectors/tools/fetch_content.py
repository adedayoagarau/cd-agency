"""Tool for fetching content from connected platforms."""
from __future__ import annotations

from typing import Any

from runtime.tools.base import Tool, ToolResult


class FetchContentTool(Tool):
    """Fetch content from external platforms via connectors."""

    name = "fetch_content"
    description = "Fetch content from external platforms via connectors"
    parameters = {
        "connector_name": {
            "type": "string",
            "description": "Name of the connector to use",
        },
        "content_id": {
            "type": "string",
            "description": "Specific content ID to fetch",
            "optional": True,
        },
        "content_type": {
            "type": "string",
            "description": "Type of content to fetch",
            "optional": True,
        },
        "limit": {
            "type": "integer",
            "description": "Max items to fetch",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        from runtime.connectors.registry import connector_registry
        from runtime.connectors.base import ContentType

        connector_name = kwargs.get("connector_name", "")
        content_id = kwargs.get("content_id")
        content_type_str = kwargs.get("content_type")
        limit = kwargs.get("limit")

        connector = connector_registry.get_connector(connector_name)
        if not connector:
            return ToolResult(
                success=False,
                error=f"Connector '{connector_name}' not found or disabled",
            )

        try:
            if content_id:
                item = connector.get_content(content_id)
                if not item:
                    return ToolResult(
                        success=False,
                        error=f"Content '{content_id}' not found",
                    )
                return ToolResult(
                    success=True,
                    data={
                        "content": [_serialize_item(item)],
                        "total": 1,
                        "connector": connector_name,
                    },
                )
            else:
                ct = None
                if content_type_str:
                    try:
                        ct = ContentType(content_type_str.lower())
                    except ValueError:
                        pass
                items = connector.list_content(
                    content_type=ct, limit=limit or 50,
                )
                return ToolResult(
                    success=True,
                    data={
                        "content": [_serialize_item(i) for i in items],
                        "total": len(items),
                        "connector": connector_name,
                    },
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


def _serialize_item(item: Any) -> dict[str, Any]:
    """Convert a ContentItem to a plain dict."""
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "content_type": item.content_type.value if item.content_type else None,
        "url": item.url,
        "tags": item.tags,
        "status": item.status,
    }

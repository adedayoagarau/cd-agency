"""Tool for pushing content to connected platforms."""
from __future__ import annotations

from typing import Any

from runtime.tools.base import Tool, ToolResult


class PushContentTool(Tool):
    """Create or update content on external platforms via connectors."""

    name = "push_content"
    description = "Create or update content on external platforms via connectors"
    parameters = {
        "connector_name": {
            "type": "string",
            "description": "Name of the connector to use",
        },
        "title": {
            "type": "string",
            "description": "Title of the content to create or update",
        },
        "content": {
            "type": "string",
            "description": "Body content to push",
        },
        "content_type": {
            "type": "string",
            "description": "Type of content (default: article)",
            "optional": True,
        },
        "content_id": {
            "type": "string",
            "description": "Content ID for updating existing content",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        from runtime.connectors.registry import connector_registry
        from runtime.connectors.base import ContentItem, ContentType

        connector_name = kwargs.get("connector_name", "")
        title = kwargs.get("title", "")
        content = kwargs.get("content", "")
        content_type_str = kwargs.get("content_type", "article")
        content_id = kwargs.get("content_id")

        connector = connector_registry.get_connector(connector_name)
        if not connector:
            return ToolResult(
                success=False,
                error=f"Connector '{connector_name}' not found or disabled",
            )

        try:
            ct = ContentType.ARTICLE
            try:
                ct = ContentType(content_type_str.lower())
            except ValueError:
                pass

            item = ContentItem(
                id=content_id or "",
                title=title,
                content=content,
                content_type=ct,
            )

            if content_id:
                result_item = connector.update_content(content_id, item)
                action = "updated"
            else:
                result_item = connector.create_content(item)
                action = "created"

            return ToolResult(
                success=True,
                data={
                    "action": action,
                    "item": _serialize_item(result_item),
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

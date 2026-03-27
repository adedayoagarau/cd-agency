"""Notion workspace connector."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any

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

_logger = logging.getLogger(__name__)

_NOTION_API = "https://api.notion.com"
_NOTION_VERSION = "2022-06-28"


class NotionConnector(BaseConnector):
    """Connector for the Notion API (pages, databases, blocks)."""

    CONNECTOR_TYPE = "notion"
    SUPPORTED_CONTENT_TYPES = [
        ContentType.ARTICLE,
        ContentType.PAGE,
        ContentType.DATABASE,
        ContentType.DOCUMENT,
    ]

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.api_token = (
            config.credentials.get("api_key")
            or config.credentials.get("api_token", "")
        )
        self.database_id = config.settings.get("database_id", "")

    # -- headers -----------------------------------------------------------

    def _get_default_headers(self) -> dict[str, str]:
        h = super()._get_default_headers()
        h["Authorization"] = f"Bearer {self.api_token}"
        h["Notion-Version"] = _NOTION_VERSION
        return h

    # -- abstract interface ------------------------------------------------

    def authenticate(self) -> bool:
        try:
            self._make_request("GET", f"{_NOTION_API}/v1/users/me")
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

    def health_check(self) -> HealthCheck:
        t0 = time.time()
        try:
            resp = self._make_request("GET", f"{_NOTION_API}/v1/users/me")
            name = resp.get("name", "unknown")
            return HealthCheck(
                status=ConnectorStatus.HEALTHY,
                message=f"Authenticated as {name}",
                latency_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return HealthCheck(
                status=ConnectorStatus.UNHEALTHY,
                message="Connection failed",
                error=str(e),
            )

    def get_schema(self) -> dict[str, Any]:
        if not self.database_id:
            return {"error": "No database_id configured"}
        try:
            resp = self._make_request(
                "GET", f"{_NOTION_API}/v1/databases/{self.database_id}"
            )
            properties = resp.get("properties", {})
            return {
                "database_id": self.database_id,
                "title": self._extract_title_from_rich_text(
                    resp.get("title", [])
                ),
                "properties": {
                    name: {
                        "type": prop.get("type", ""),
                        "id": prop.get("id", ""),
                    }
                    for name, prop in properties.items()
                },
            }
        except Exception as e:
            return {"error": str(e)}

    def list_content(
        self,
        content_type: ContentType | None = None,
        limit: int = 50,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[ContentItem]:
        """List pages from a database or via search.

        If ``database_id`` is configured, queries that database. Otherwise
        uses the Notion search API.
        """
        try:
            if self.database_id:
                body: dict[str, Any] = {"page_size": min(limit, 100)}
                if filters and "filter" in filters:
                    body["filter"] = filters["filter"]
                resp = self._make_request(
                    "POST",
                    f"{_NOTION_API}/v1/databases/{self.database_id}/query",
                    data=body,
                )
            else:
                body = {
                    "page_size": min(limit, 100),
                    "filter": {"property": "object", "value": "page"},
                }
                if filters and "search" in filters:
                    body["query"] = filters["search"]
                resp = self._make_request(
                    "POST",
                    f"{_NOTION_API}/v1/search",
                    data=body,
                )
            results = resp.get("results", [])
            return [self._parse_page(p) for p in results]
        except Exception:
            return []

    def get_content(self, content_id: str) -> ContentItem | None:
        """Retrieve a Notion page and its block children."""
        try:
            page = self._make_request(
                "GET", f"{_NOTION_API}/v1/pages/{content_id}"
            )
            # Fetch first 100 blocks for page content
            blocks_resp = self._make_request(
                "GET",
                f"{_NOTION_API}/v1/blocks/{content_id}/children?page_size=100",
            )
            blocks = blocks_resp.get("results", [])
            content = self._blocks_to_text(blocks)

            item = self._parse_page(page)
            item.content = content
            item.raw_data["blocks"] = blocks
            return item
        except Exception:
            return None

    def create_content(self, item: ContentItem) -> ContentItem:
        """Create a new Notion page."""
        parent: dict[str, Any]
        if self.database_id:
            parent = {"database_id": self.database_id}
        else:
            raise NotImplementedError(
                "Creating pages without a database_id is not supported"
            )

        properties: dict[str, Any] = {}
        if item.title:
            properties["Name"] = {
                "title": [{"text": {"content": item.title}}]
            }

        body: dict[str, Any] = {"parent": parent, "properties": properties}

        # Add content as paragraph blocks
        if item.content:
            body["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": item.content}}]
                    },
                }
            ]

        resp = self._make_request("POST", f"{_NOTION_API}/v1/pages", data=body)
        return self._parse_page(resp)

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        """Update a Notion page's properties."""
        properties: dict[str, Any] = {}
        if item.title:
            properties["Name"] = {
                "title": [{"text": {"content": item.title}}]
            }

        body: dict[str, Any] = {"properties": properties}
        resp = self._make_request(
            "PATCH",
            f"{_NOTION_API}/v1/pages/{content_id}",
            data=body,
        )
        return self._parse_page(resp)

    def delete_content(self, content_id: str) -> bool:
        """Archive a Notion page (Notion does not support hard deletes)."""
        try:
            self._make_request(
                "PATCH",
                f"{_NOTION_API}/v1/pages/{content_id}",
                data={"archived": True},
            )
            return True
        except Exception:
            return False

    # -- helpers -----------------------------------------------------------

    def _parse_page(self, page: dict) -> ContentItem:
        """Convert a Notion page object to a ContentItem."""
        page_id = page.get("id", "")
        properties = page.get("properties", {})

        # Extract title from properties
        title = ""
        for prop in properties.values():
            if prop.get("type") == "title":
                title = self._extract_title_from_rich_text(
                    prop.get("title", [])
                )
                break

        created_at = updated_at = None
        if page.get("created_time"):
            created_at = datetime.fromisoformat(
                page["created_time"].replace("Z", "+00:00")
            )
        if page.get("last_edited_time"):
            updated_at = datetime.fromisoformat(
                page["last_edited_time"].replace("Z", "+00:00")
            )

        url = page.get("url", "")
        status = "archived" if page.get("archived") else "active"

        return ContentItem(
            id=page_id,
            title=title or page_id,
            content=None,
            content_type=ContentType.PAGE,
            metadata={
                "notion_id": page_id,
                "object": page.get("object", "page"),
                "parent_type": (
                    page.get("parent", {}).get("type", "")
                ),
                "property_names": list(properties.keys()),
            },
            created_at=created_at,
            updated_at=updated_at,
            url=url,
            status=status,
            raw_data=page,
            connector_id=self.name,
        )

    def _extract_title_from_rich_text(self, rich_text: list[dict]) -> str:
        """Extract plain text from a Notion rich_text array."""
        parts: list[str] = []
        for segment in rich_text:
            if segment.get("type") == "text":
                parts.append(segment.get("text", {}).get("content", ""))
            else:
                parts.append(segment.get("plain_text", ""))
        return "".join(parts)

    def _blocks_to_text(self, blocks: list[dict]) -> str:
        """Convert a list of Notion blocks to plain text."""
        lines: list[str] = []
        for block in blocks:
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})
            rich_text = block_data.get("rich_text", [])
            text = self._extract_title_from_rich_text(rich_text)
            if text:
                lines.append(text)
        return "\n".join(lines)

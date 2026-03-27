"""Contentful CMS connector."""
from __future__ import annotations

import json
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


class ContentfulConnector(BaseConnector):
    """Read-only connector for the Contentful Delivery / Preview API."""

    CONNECTOR_TYPE = "contentful"
    SUPPORTED_CONTENT_TYPES = [ContentType.ARTICLE, ContentType.PAGE, ContentType.COMPONENT]

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.space_id = config.credentials.get("space_id", "")
        self.access_token = config.credentials.get("access_token", "")
        self.environment = config.credentials.get("environment", "master")
        self.locale = config.settings.get("locale", "en-US")
        self.include_drafts = config.settings.get("include_drafts", False)
        host = "preview.contentful.com" if self.include_drafts else "cdn.contentful.com"
        self._api_base = (
            f"https://{host}/spaces/{self.space_id}"
            f"/environments/{self.environment}"
        )

    # -- headers -----------------------------------------------------------

    def _get_default_headers(self) -> dict[str, str]:
        h = super()._get_default_headers()
        h["Authorization"] = f"Bearer {self.access_token}"
        return h

    # -- abstract interface ------------------------------------------------

    def authenticate(self) -> bool:
        try:
            self._make_request("GET", f"{self._api_base}/content_types?limit=1")
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

    def health_check(self) -> HealthCheck:
        t0 = time.time()
        try:
            self._make_request("GET", f"{self._api_base}/entries?limit=1")
            return HealthCheck(
                status=ConnectorStatus.HEALTHY,
                message=f"Connected to space {self.space_id}",
                latency_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return HealthCheck(
                status=ConnectorStatus.UNHEALTHY,
                message="Connection failed",
                error=str(e),
            )

    def get_schema(self) -> dict[str, Any]:
        try:
            resp = self._make_request("GET", f"{self._api_base}/content_types")
            schema: dict[str, Any] = {"content_types": {}}
            for item in resp.get("items", []):
                ct_id = item["sys"]["id"]
                schema["content_types"][ct_id] = {
                    "name": item.get("name"),
                    "description": item.get("description"),
                    "fields": [
                        {
                            "id": f["id"],
                            "name": f.get("name"),
                            "type": f.get("type"),
                            "required": f.get("required", False),
                        }
                        for f in item.get("fields", [])
                    ],
                }
            return schema
        except Exception as e:
            return {"error": str(e)}

    def list_content(
        self,
        content_type: ContentType | None = None,
        limit: int | None = None,
        offset: int | None = None,
        filters: dict[str, Any] | None = None,
        since: datetime | None = None,
    ) -> list[ContentItem]:
        params: dict[str, str] = {
            "locale": self.locale,
            "limit": str(min(limit or 100, 1000)),
        }
        if offset:
            params["skip"] = str(offset)
        if since:
            params["sys.updatedAt[gte]"] = since.isoformat()
        if filters:
            if "content_type" in filters:
                params["content_type"] = filters["content_type"]
            if "search" in filters:
                params["query"] = filters["search"]
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        try:
            resp = self._make_request("GET", f"{self._api_base}/entries?{qs}")
            return [self._parse_entry(e) for e in resp.get("items", [])]
        except Exception:
            return []

    def get_content(self, content_id: str) -> ContentItem | None:
        try:
            resp = self._make_request(
                "GET",
                f"{self._api_base}/entries/{content_id}?locale={self.locale}",
            )
            return self._parse_entry(resp)
        except Exception:
            return None

    def create_content(self, item: ContentItem) -> ContentItem:
        raise NotImplementedError("Contentful Delivery API is read-only")

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        raise NotImplementedError("Contentful Delivery API is read-only")

    def delete_content(self, content_id: str) -> bool:
        raise NotImplementedError("Contentful Delivery API is read-only")

    # -- helpers -----------------------------------------------------------

    def _parse_entry(self, entry: dict) -> ContentItem:
        sys = entry.get("sys", {})
        fields = entry.get("fields", {})

        title = (
            fields.get("title")
            or fields.get("name")
            or fields.get("headline")
            or sys.get("id", "")
        )
        content = (
            fields.get("content")
            or fields.get("body")
            or fields.get("description")
            or ""
        )
        if isinstance(content, dict) and "nodeType" in content:
            content = self._extract_rich_text(content)

        created_at = updated_at = None
        if sys.get("createdAt"):
            created_at = datetime.fromisoformat(
                sys["createdAt"].replace("Z", "+00:00")
            )
        if sys.get("updatedAt"):
            updated_at = datetime.fromisoformat(
                sys["updatedAt"].replace("Z", "+00:00")
            )

        return ContentItem(
            id=sys.get("id", ""),
            title=str(title),
            content=str(content) if content else None,
            content_type=ContentType.ARTICLE,
            metadata={
                "contentful_id": sys.get("id"),
                "content_type_id": (
                    sys.get("contentType", {}).get("sys", {}).get("id")
                ),
                "locale": self.locale,
                "fields": list(fields.keys()),
            },
            created_at=created_at,
            updated_at=updated_at,
            raw_data=entry,
            connector_id=self.name,
        )

    def _extract_rich_text(self, node: dict) -> str:
        """Recursively extract plain text from a Contentful rich-text tree."""
        if not isinstance(node, dict):
            return str(node)
        if node.get("nodeType") == "text":
            return node.get("value", "")
        return "".join(self._extract_rich_text(c) for c in node.get("content", []))

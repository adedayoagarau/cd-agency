"""Sanity CMS connector (stub)."""
from __future__ import annotations

from typing import Any

from runtime.connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorStatus,
    ContentItem,
    ContentType,
    HealthCheck,
)


class SanityConnector(BaseConnector):
    """Stub connector for Sanity CMS — not yet implemented."""

    CONNECTOR_TYPE = "sanity"
    SUPPORTED_CONTENT_TYPES = [ContentType.ARTICLE, ContentType.PAGE, ContentType.DOCUMENT]

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)

    def authenticate(self) -> bool:
        return False

    def health_check(self) -> HealthCheck:
        return HealthCheck(
            status=ConnectorStatus.UNHEALTHY,
            message="Sanity connector not yet implemented",
        )

    def get_schema(self) -> dict[str, Any]:
        return {}

    def list_content(
        self,
        content_type: ContentType | None = None,
        limit: int = 50,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
    ) -> list[ContentItem]:
        return []

    def get_content(self, content_id: str) -> ContentItem | None:
        return None

    def create_content(self, item: ContentItem) -> ContentItem:
        raise NotImplementedError("Sanity connector not yet implemented")

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        raise NotImplementedError("Sanity connector not yet implemented")

    def delete_content(self, content_id: str) -> bool:
        raise NotImplementedError("Sanity connector not yet implemented")

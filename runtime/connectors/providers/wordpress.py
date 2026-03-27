"""WordPress REST API connector (stub)."""
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


class WordPressConnector(BaseConnector):
    """Stub connector for WordPress — not yet implemented."""

    CONNECTOR_TYPE = "wordpress"
    SUPPORTED_CONTENT_TYPES = [ContentType.ARTICLE, ContentType.PAGE]

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)

    def authenticate(self) -> bool:
        return False

    def health_check(self) -> HealthCheck:
        return HealthCheck(
            status=ConnectorStatus.UNHEALTHY,
            message="WordPress connector not yet implemented",
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
        raise NotImplementedError("WordPress connector not yet implemented")

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        raise NotImplementedError("WordPress connector not yet implemented")

    def delete_content(self, content_id: str) -> bool:
        raise NotImplementedError("WordPress connector not yet implemented")

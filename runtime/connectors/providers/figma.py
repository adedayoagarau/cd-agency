"""Figma design platform connector."""
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

_FIGMA_API = "https://api.figma.com"


class FigmaConnector(BaseConnector):
    """Read-only connector for the Figma REST API."""

    CONNECTOR_TYPE = "figma"
    SUPPORTED_CONTENT_TYPES = [ContentType.DESIGN, ContentType.COMPONENT, ContentType.FILE]

    def __init__(self, config: ConnectorConfig) -> None:
        super().__init__(config)
        self.access_token = (
            config.credentials.get("personal_access_token")
            or config.credentials.get("access_token", "")
        )
        self.team_id = config.settings.get("team_id", "")
        self.file_key = config.settings.get("file_key", "")

    # -- headers -----------------------------------------------------------

    def _get_default_headers(self) -> dict[str, str]:
        h = super()._get_default_headers()
        h["X-Figma-Token"] = self.access_token
        # Remove Bearer auth set by parent; Figma uses its own header
        h.pop("Authorization", None)
        return h

    # -- abstract interface ------------------------------------------------

    def authenticate(self) -> bool:
        try:
            self._make_request("GET", f"{_FIGMA_API}/v1/me")
            self._authenticated = True
            return True
        except Exception:
            self._authenticated = False
            return False

    def health_check(self) -> HealthCheck:
        t0 = time.time()
        try:
            resp = self._make_request("GET", f"{_FIGMA_API}/v1/me")
            user = resp.get("handle", "unknown")
            return HealthCheck(
                status=ConnectorStatus.HEALTHY,
                message=f"Authenticated as {user}",
                latency_ms=(time.time() - t0) * 1000,
            )
        except Exception as e:
            return HealthCheck(
                status=ConnectorStatus.UNHEALTHY,
                message="Connection failed",
                error=str(e),
            )

    def get_schema(self) -> dict[str, Any]:
        if not self.file_key:
            return {"error": "No file_key configured"}
        try:
            resp = self._make_request(
                "GET", f"{_FIGMA_API}/v1/files/{self.file_key}?depth=1"
            )
            components = resp.get("components", {})
            return {
                "file_name": resp.get("name", ""),
                "last_modified": resp.get("lastModified", ""),
                "components": {
                    cid: {
                        "name": info.get("name", ""),
                        "description": info.get("description", ""),
                    }
                    for cid, info in components.items()
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
        """List Figma files.

        If ``team_id`` is configured, fetches team projects and their files.
        Otherwise, returns the single configured file (if ``file_key`` is set).
        """
        items: list[ContentItem] = []

        if self.team_id:
            try:
                projects_resp = self._make_request(
                    "GET",
                    f"{_FIGMA_API}/v1/teams/{self.team_id}/projects",
                )
                for project in projects_resp.get("projects", []):
                    pid = project.get("id", "")
                    try:
                        files_resp = self._make_request(
                            "GET",
                            f"{_FIGMA_API}/v1/projects/{pid}/files",
                        )
                        for f in files_resp.get("files", []):
                            items.append(self._file_to_item(f))
                    except Exception:
                        _logger.debug("Failed to list files for project %s", pid)
            except Exception:
                _logger.debug("Failed to list team projects")
        elif self.file_key:
            item = self.get_content(self.file_key)
            if item is not None:
                items.append(item)

        # Apply offset / limit
        return items[offset : offset + limit]

    def get_content(self, content_id: str) -> ContentItem | None:
        """Get a Figma file or node.

        *content_id* may be a bare ``file_key`` or ``file_key:node_id``.
        """
        file_key = content_id
        node_id: str | None = None
        if ":" in content_id:
            file_key, node_id = content_id.split(":", 1)

        try:
            if node_id:
                resp = self._make_request(
                    "GET",
                    f"{_FIGMA_API}/v1/files/{file_key}/nodes?ids={node_id}",
                )
                nodes = resp.get("nodes", {})
                node_data = nodes.get(node_id, {})
                document = node_data.get("document", {})
                return ContentItem(
                    id=content_id,
                    title=document.get("name", content_id),
                    content=None,
                    content_type=ContentType.COMPONENT,
                    metadata={
                        "file_key": file_key,
                        "node_id": node_id,
                        "type": document.get("type", ""),
                    },
                    raw_data=node_data,
                    connector_id=self.name,
                )
            else:
                resp = self._make_request(
                    "GET",
                    f"{_FIGMA_API}/v1/files/{file_key}?depth=1",
                )
                last_modified = None
                if resp.get("lastModified"):
                    try:
                        last_modified = datetime.fromisoformat(
                            resp["lastModified"].replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass
                return ContentItem(
                    id=file_key,
                    title=resp.get("name", file_key),
                    content=None,
                    content_type=ContentType.FILE,
                    metadata={
                        "file_key": file_key,
                        "version": resp.get("version", ""),
                        "component_count": len(resp.get("components", {})),
                    },
                    updated_at=last_modified,
                    raw_data=resp,
                    connector_id=self.name,
                )
        except Exception:
            return None

    def create_content(self, item: ContentItem) -> ContentItem:
        raise NotImplementedError("Figma API is read-only for content creation")

    def update_content(self, content_id: str, item: ContentItem) -> ContentItem:
        raise NotImplementedError("Figma API is read-only for content updates")

    def delete_content(self, content_id: str) -> bool:
        raise NotImplementedError("Figma API is read-only for content deletion")

    # -- helpers -----------------------------------------------------------

    def _file_to_item(self, file_data: dict) -> ContentItem:
        """Convert a Figma file listing entry to a ContentItem."""
        last_modified = None
        if file_data.get("last_modified"):
            try:
                last_modified = datetime.fromisoformat(
                    file_data["last_modified"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass
        return ContentItem(
            id=file_data.get("key", ""),
            title=file_data.get("name", ""),
            content=None,
            content_type=ContentType.FILE,
            metadata={"file_key": file_data.get("key", "")},
            updated_at=last_modified,
            raw_data=file_data,
            connector_id=self.name,
        )

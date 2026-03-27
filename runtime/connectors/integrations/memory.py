"""Memory integration for connector content."""
from __future__ import annotations

import logging
from typing import Any

from runtime.connectors.base import ContentItem

_logger = logging.getLogger(__name__)


class ConnectorMemoryBridge:
    """Bridges connector content with the project memory system."""

    def __init__(self, memory=None) -> None:
        self._memory = memory

    def store_content_signals(self, item: ContentItem, signals: dict[str, Any]) -> bool:
        """Store extracted signals in project memory."""
        if self._memory is None:
            try:
                from runtime.memory import ProjectMemory
                self._memory = ProjectMemory()
            except Exception:
                _logger.debug("Project memory not available")
                return False
        try:
            key = f"connector:{item.connector_id}:{item.id}"
            entry = {
                "source": item.connector_id or "unknown",
                "content_type": item.content_type.value if item.content_type else "unknown",
                "title": item.title or "",
                "signals": signals,
            }
            # Use remember method if available
            if hasattr(self._memory, "remember"):
                self._memory.remember(
                    category="connectors",
                    key=key,
                    value=str(entry),
                )
            return True
        except Exception as exc:
            _logger.debug("Failed to store in memory: %s", exc)
            return False

    def get_connector_context(self, connector_id: str) -> str:
        """Build context string from stored connector content."""
        if self._memory is None:
            return ""
        try:
            if hasattr(self._memory, "recall"):
                results = self._memory.recall(f"connector:{connector_id}")
                if results:
                    return f"## Content from {connector_id}\n{results}"
        except Exception:
            pass
        return ""

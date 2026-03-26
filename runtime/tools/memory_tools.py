"""Memory tools — let agents read from and write to ProjectMemory."""

from __future__ import annotations

from typing import Any

from runtime.tools.base import Tool, ToolResult


class RememberContext(Tool):
    """Store context in project memory for future agent runs."""

    name = "remember_context"
    description = (
        "Save a piece of context to project memory so future agent runs can recall it. "
        "Use for terminology decisions, voice preferences, content patterns, or any "
        "decision that should persist across sessions."
    )
    parameters = {
        "key": {"type": "string", "description": "Short identifier for this memory (e.g. 'error-tone')"},
        "value": {"type": "string", "description": "The content to remember"},
        "category": {
            "type": "string",
            "description": "Category: terminology, voice, pattern, or decision",
            "optional": True,
        },
    }

    def __init__(self, memory: Any = None) -> None:
        self._memory = memory

    def _get_memory(self) -> Any:
        if self._memory is None:
            from runtime.memory import ProjectMemory
            self._memory = ProjectMemory.load()
        return self._memory

    def execute(self, **kwargs: Any) -> ToolResult:
        key = kwargs.get("key", "")
        value = kwargs.get("value", "")
        category = kwargs.get("category", "decision")

        if not key or not value:
            return ToolResult(success=False, error="Both key and value are required")

        memory = self._get_memory()
        memory.remember(key=key, value=value, category=category, source_agent="tool")

        return ToolResult(
            success=True,
            data={"key": key, "category": category, "stored": True},
        )


class RecallContext(Tool):
    """Search project memory for relevant context."""

    name = "recall_context"
    description = (
        "Search project memory for relevant past context. Uses semantic search "
        "when available, falls back to substring matching. Useful for finding "
        "past terminology decisions, content patterns, or voice preferences."
    )
    parameters = {
        "query": {"type": "string", "description": "What to search for in memory"},
    }

    def __init__(self, memory: Any = None) -> None:
        self._memory = memory

    def _get_memory(self) -> Any:
        if self._memory is None:
            from runtime.memory import ProjectMemory
            self._memory = ProjectMemory.load()
        return self._memory

    def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="No query provided")

        memory = self._get_memory()
        results = memory.search(query)

        entries = [
            {"key": e.key, "value": e.value, "category": e.category}
            for e in results[:10]
        ]

        return ToolResult(
            success=True,
            data={"query": query, "results": entries, "count": len(entries)},
        )


class RecallBrandVoice(Tool):
    """Retrieve brand voice decisions from project memory."""

    name = "recall_brand_voice"
    description = (
        "Retrieve all brand voice and terminology decisions from project memory. "
        "Returns voice guidelines, tone preferences, and terminology standards."
    )
    parameters = {}

    def __init__(self, memory: Any = None) -> None:
        self._memory = memory

    def _get_memory(self) -> Any:
        if self._memory is None:
            from runtime.memory import ProjectMemory
            self._memory = ProjectMemory.load()
        return self._memory

    def execute(self, **kwargs: Any) -> ToolResult:
        memory = self._get_memory()

        voice_entries = memory.recall_by_category("voice")
        term_entries = memory.recall_by_category("terminology")

        data: dict[str, Any] = {}
        if voice_entries:
            data["voice"] = [
                {"key": e.key, "value": e.value} for e in voice_entries
            ]
        if term_entries:
            data["terminology"] = [
                {"key": e.key, "value": e.value} for e in term_entries
            ]
        data["total"] = len(voice_entries) + len(term_entries)

        return ToolResult(success=True, data=data)

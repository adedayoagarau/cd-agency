"""Tool registry — central lookup for all available tools."""

from __future__ import annotations

from typing import Any

from runtime.tools.base import Tool


# Default tool-to-agent mapping: which tools each agent type gets
_DEFAULT_AGENT_TOOLS: dict[str, list[str]] = {
    "error-message-architect": [
        "run_linter", "score_readability", "check_accessibility",
        "read_file", "recall_context", "remember_context",
    ],
    "microcopy-review-agent": [
        "run_linter", "score_readability", "check_accessibility",
        "recall_context", "recall_brand_voice",
    ],
    "tone-evaluation-agent": [
        "check_voice_consistency", "recall_brand_voice", "recall_context",
    ],
    "accessibility-content-auditor": [
        "check_accessibility", "score_readability", "run_linter",
    ],
    "brand-voice-archaeologist": [
        "extract_brand_patterns", "query_brand_dna",
        "recall_context", "remember_context", "recall_brand_voice", "read_file",
    ],
}


class ToolRegistry:
    """Central registry for all available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """Look up a tool by name."""
        return self._tools.get(name)

    def get_tools_for_agent(self, agent_slug: str) -> list[Tool]:
        """Return tools configured for a specific agent."""
        tool_names = _DEFAULT_AGENT_TOOLS.get(agent_slug, [])
        return [self._tools[n] for n in tool_names if n in self._tools]

    def get_tools_by_names(self, names: list[str]) -> list[Tool]:
        """Return tools matching the given names."""
        return [self._tools[n] for n in names if n in self._tools]

    def get_all_schemas(self) -> list[dict[str, Any]]:
        """Return LLM tool schemas for all registered tools."""
        return [t.to_llm_tool_schema() for t in self._tools.values()]

    def list_all(self) -> list[Tool]:
        """Return all registered tools."""
        return list(self._tools.values())

    @property
    def count(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return self.count


def build_default_registry() -> ToolRegistry:
    """Build a registry with all default tools pre-registered."""
    from runtime.tools.content_tools import (
        RunLinter,
        ScoreReadability,
        CheckAccessibility,
        CheckVoiceConsistency,
    )
    from runtime.tools.file_tools import ReadFile, WriteFile, ListDirectory, SearchFiles
    from runtime.tools.memory_tools import RememberContext, RecallContext, RecallBrandVoice
    from runtime.tools.brand_tools import ExtractBrandPatterns, QueryBrandDNA

    registry = ToolRegistry()
    registry.register(RunLinter())
    registry.register(ScoreReadability())
    registry.register(CheckAccessibility())
    registry.register(CheckVoiceConsistency())
    registry.register(ReadFile())
    registry.register(WriteFile())
    registry.register(ListDirectory())
    registry.register(SearchFiles())
    registry.register(RememberContext())
    registry.register(RecallContext())
    registry.register(RecallBrandVoice())
    registry.register(ExtractBrandPatterns())
    registry.register(QueryBrandDNA())
    return registry

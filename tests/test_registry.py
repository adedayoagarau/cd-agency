"""Tests for the AgentRegistry."""

from pathlib import Path

import pytest

from runtime.agent import Agent, AgentInput
from runtime.registry import AgentRegistry


AGENTS_DIR = Path(__file__).parent.parent / "content-design"


def _make_agent(name: str, slug_file: str, tags: list[str] | None = None, difficulty: str = "intermediate") -> Agent:
    return Agent(
        name=name,
        description=f"Description of {name}",
        tags=tags or [],
        difficulty_level=difficulty,
        source_file=f"content-design/{slug_file}.md",
    )


class TestRegistryBasics:
    def test_register_and_get(self):
        registry = AgentRegistry()
        agent = _make_agent("Error Architect", "error-message-architect", tags=["errors"])
        registry.register(agent)
        assert registry.get("error-message-architect") is agent

    def test_get_by_alias(self):
        registry = AgentRegistry()
        agent = _make_agent("Error Architect", "error-message-architect")
        registry.register(agent)
        assert registry.get("error") is agent
        assert registry.get("errors") is agent

    def test_get_by_name(self):
        registry = AgentRegistry()
        agent = _make_agent("Error Architect", "error-message-architect")
        registry.register(agent)
        assert registry.get("error architect") is agent

    def test_get_unknown_returns_none(self):
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_count(self):
        registry = AgentRegistry([
            _make_agent("A", "a"),
            _make_agent("B", "b"),
        ])
        assert registry.count == 2
        assert len(registry) == 2

    def test_contains(self):
        registry = AgentRegistry([_make_agent("A", "error-message-architect")])
        assert "error-message-architect" in registry
        assert "error" in registry  # alias
        assert "nonexistent" not in registry


class TestRegistryFiltering:
    def test_filter_by_tag(self):
        registry = AgentRegistry([
            _make_agent("A", "a", tags=["errors", "validation"]),
            _make_agent("B", "b", tags=["tone", "brand"]),
            _make_agent("C", "c", tags=["errors", "recovery"]),
        ])
        results = registry.filter_by_tag("errors")
        assert len(results) == 2

    def test_filter_by_difficulty(self):
        registry = AgentRegistry([
            _make_agent("A", "a", difficulty="beginner"),
            _make_agent("B", "b", difficulty="advanced"),
            _make_agent("C", "c", difficulty="beginner"),
        ])
        results = registry.filter_by_difficulty("beginner")
        assert len(results) == 2

    def test_search(self):
        registry = AgentRegistry([
            _make_agent("Error Message Architect", "error-message-architect", tags=["errors"]),
            _make_agent("Tone Evaluation Agent", "tone-evaluation-agent", tags=["tone"]),
        ])
        results = registry.search("error")
        assert len(results) == 1
        assert results[0].name == "Error Message Architect"

    def test_search_by_tag(self):
        registry = AgentRegistry([
            _make_agent("A", "a", tags=["mobile", "app"]),
            _make_agent("B", "b", tags=["desktop"]),
        ])
        results = registry.search("mobile")
        assert len(results) == 1

    def test_list_all_sorted(self):
        registry = AgentRegistry([
            _make_agent("Zebra", "z"),
            _make_agent("Alpha", "a"),
            _make_agent("Middle", "m"),
        ])
        names = [a.name for a in registry.list_all()]
        assert names == ["Alpha", "Middle", "Zebra"]


class TestRegistryCustomAlias:
    def test_add_alias(self):
        registry = AgentRegistry([_make_agent("Agent", "my-agent")])
        registry.add_alias("shortcut", "my-agent")
        assert registry.get("shortcut") is not None


class TestRegistryFromDirectory:
    def test_loads_all_agents(self):
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        assert registry.count == 18

    def test_all_default_aliases_resolve(self):
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        aliases_that_should_work = [
            "generalist", "error", "microcopy", "tone", "a11y",
            "cta", "onboarding", "docs", "mobile", "l10n",
            "notifications", "privacy", "empty", "search", "chatbot",
        ]
        for alias in aliases_that_should_work:
            agent = registry.get(alias)
            assert agent is not None, f"Alias '{alias}' did not resolve to an agent"

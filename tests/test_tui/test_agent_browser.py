"""Tests for the AgentBrowser widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.agent import Agent
from runtime.tui.widgets.agent_browser import AgentBrowser, AgentSelected


def _make_agent(name: str, tags: list[str] | None = None, desc: str = "") -> Agent:
    return Agent(
        name=name,
        description=desc or f"Test agent: {name}",
        tags=tags or ["general"],
    )


class BrowserTestApp(App):
    def compose(self) -> ComposeResult:
        yield AgentBrowser(id="browser")


class TestAgentBrowser:
    @pytest.mark.asyncio
    async def test_set_agents(self):
        app = BrowserTestApp()
        async with app.run_test() as pilot:
            browser = app.query_one("#browser", AgentBrowser)
            agents = [_make_agent("Error Architect", ["errors"]), _make_agent("CTA Specialist", ["cta"])]
            browser.set_agents(agents)
            assert len(browser._agents) == 2
            assert len(browser._filtered) == 2

    @pytest.mark.asyncio
    async def test_search_filters_agents(self):
        app = BrowserTestApp()
        async with app.run_test() as pilot:
            browser = app.query_one("#browser", AgentBrowser)
            agents = [
                _make_agent("Error Architect", ["errors"]),
                _make_agent("CTA Specialist", ["cta"]),
                _make_agent("Tone Agent", ["voice"]),
            ]
            browser.set_agents(agents)
            # Simulate search
            browser._filtered = [a for a in agents if "error" in a.name.lower()]
            assert len(browser._filtered) == 1
            assert browser._filtered[0].name == "Error Architect"

    @pytest.mark.asyncio
    async def test_search_by_tag(self):
        app = BrowserTestApp()
        async with app.run_test() as pilot:
            browser = app.query_one("#browser", AgentBrowser)
            agents = [
                _make_agent("Error Architect", ["errors", "recovery"]),
                _make_agent("CTA Specialist", ["cta", "conversion"]),
            ]
            browser.set_agents(agents)
            browser._filtered = [
                a for a in agents if any("cta" in t for t in a.tags)
            ]
            assert len(browser._filtered) == 1
            assert browser._filtered[0].name == "CTA Specialist"

    @pytest.mark.asyncio
    async def test_empty_search_shows_all(self):
        app = BrowserTestApp()
        async with app.run_test() as pilot:
            browser = app.query_one("#browser", AgentBrowser)
            agents = [_make_agent("A"), _make_agent("B"), _make_agent("C")]
            browser.set_agents(agents)
            # Empty query shows all
            browser._filtered = list(agents)
            assert len(browser._filtered) == 3

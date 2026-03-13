"""Tests for the AgentOutputPanel widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.tui.widgets.agent_output import AgentOutputPanel


class OutputTestApp(App):
    def compose(self) -> ComposeResult:
        yield AgentOutputPanel(id="output")


class TestAgentOutputPanel:
    @pytest.mark.asyncio
    async def test_mounts(self):
        app = OutputTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#output", AgentOutputPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_show_output(self):
        app = OutputTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#output", AgentOutputPanel)
            panel.show_output("Revised content here", input_text="Original content")
            assert panel._current_output == "Revised content here"
            assert panel._input_text == "Original content"

    @pytest.mark.asyncio
    async def test_show_output_no_input(self):
        app = OutputTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#output", AgentOutputPanel)
            panel.show_output("Agent output text")
            assert panel._current_output == "Agent output text"
            assert panel._input_text == ""

    @pytest.mark.asyncio
    async def test_clear(self):
        app = OutputTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#output", AgentOutputPanel)
            panel.show_output("Some output")
            panel.clear()
            assert panel._current_output == ""
            assert panel._input_text == ""

    @pytest.mark.asyncio
    async def test_show_loading(self):
        app = OutputTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#output", AgentOutputPanel)
            panel.show_loading()
            # Should not raise

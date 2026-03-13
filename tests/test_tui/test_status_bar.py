"""Tests for the StatusBar widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.tui.widgets.status_bar import StatusBar


class StatusTestApp(App):
    def compose(self) -> ComposeResult:
        yield StatusBar(id="status")


class TestStatusBar:
    @pytest.mark.asyncio
    async def test_mounts(self):
        app = StatusTestApp()
        async with app.run_test() as pilot:
            status = app.query_one("#status", StatusBar)
            assert status is not None

    @pytest.mark.asyncio
    async def test_set_agent(self):
        app = StatusTestApp()
        async with app.run_test() as pilot:
            status = app.query_one("#status", StatusBar)
            status.set_agent("Error Message Architect")
            assert status._agent == "Error Message Architect"

    @pytest.mark.asyncio
    async def test_set_preset(self):
        app = StatusTestApp()
        async with app.run_test() as pilot:
            status = app.query_one("#status", StatusBar)
            status.set_preset("Material Design")
            assert status._preset == "Material Design"

    @pytest.mark.asyncio
    async def test_set_tokens(self):
        app = StatusTestApp()
        async with app.run_test() as pilot:
            status = app.query_one("#status", StatusBar)
            status.set_tokens(1500)
            assert status._tokens == 1500

    @pytest.mark.asyncio
    async def test_set_memory_count(self):
        app = StatusTestApp()
        async with app.run_test() as pilot:
            status = app.query_one("#status", StatusBar)
            status.set_memory_count(5)
            assert status._memory_count == 5

    @pytest.mark.asyncio
    async def test_set_mode(self):
        app = StatusTestApp()
        async with app.run_test() as pilot:
            status = app.query_one("#status", StatusBar)
            status.set_mode("Form")
            assert status._mode == "Form"

"""Tests for the main StudioApp."""

from __future__ import annotations

import pytest

from runtime.tui.app import StudioApp
from runtime.tui.widgets.agent_browser import AgentBrowser
from runtime.tui.widgets.chat_panel import ChatPanel
from runtime.tui.widgets.content_editor import ContentEditor
from runtime.tui.widgets.memory_panel import MemoryPanel
from runtime.tui.widgets.scoring_panel import ScoringPanel
from runtime.tui.widgets.status_bar import StatusBar


@pytest.fixture
def app():
    return StudioApp(preset="test-preset", initial_content="Hello world")


class TestStudioApp:
    """Tests for StudioApp mounting and key bindings."""

    @pytest.mark.asyncio
    async def test_app_mounts(self, app):
        """App should mount without errors and contain all panels."""
        async with app.run_test() as pilot:
            assert app.query_one("#agent-browser", AgentBrowser) is not None
            assert app.query_one("#chat-panel", ChatPanel) is not None
            assert app.query_one("#content-editor", ContentEditor) is not None
            assert app.query_one("#scoring-panel", ScoringPanel) is not None
            assert app.query_one("#status-bar", StatusBar) is not None
            assert app.query_one("#memory-panel", MemoryPanel) is not None

    @pytest.mark.asyncio
    async def test_initial_content(self, app):
        """Content editor should load initial content."""
        async with app.run_test() as pilot:
            editor = app.query_one("#content-editor", ContentEditor)
            assert editor.text == "Hello world"

    @pytest.mark.asyncio
    async def test_preset_in_status_bar(self, app):
        """Status bar should show the preset name."""
        async with app.run_test() as pilot:
            status = app.query_one("#status-bar", StatusBar)
            assert status._preset == "test-preset"

    @pytest.mark.asyncio
    async def test_toggle_mode(self, app):
        """Ctrl+T should toggle between Chat and Form mode."""
        async with app.run_test() as pilot:
            status = app.query_one("#status-bar", StatusBar)
            assert status._mode == "Chat"
            app.action_toggle_mode()
            assert status._mode == "Form"
            app.action_toggle_mode()
            assert status._mode == "Chat"

    @pytest.mark.asyncio
    async def test_toggle_memory(self, app):
        """Ctrl+M should toggle memory panel visibility."""
        async with app.run_test() as pilot:
            browser = app.query_one("#agent-browser", AgentBrowser)
            memory = app.query_one("#memory-panel", MemoryPanel)
            assert browser.display is True
            assert memory.display is False
            app.action_toggle_memory()
            assert browser.display is False
            assert memory.display is True
            app.action_toggle_memory()
            assert browser.display is True
            assert memory.display is False

    @pytest.mark.asyncio
    async def test_toggle_sidebar(self, app):
        """Ctrl+B should toggle sidebar visibility."""
        async with app.run_test() as pilot:
            browser = app.query_one("#agent-browser", AgentBrowser)
            assert browser.display is True
            app.action_toggle_sidebar()
            assert browser.display is False

    @pytest.mark.asyncio
    async def test_switch_preset(self, app):
        """switch_preset should update status bar."""
        async with app.run_test() as pilot:
            app.switch_preset("Apple HIG")
            status = app.query_one("#status-bar", StatusBar)
            assert status._preset == "Apple HIG"

    @pytest.mark.asyncio
    async def test_switch_mode_to(self, app):
        """switch_mode_to should set specific mode."""
        async with app.run_test() as pilot:
            app.switch_mode_to("Form")
            status = app.query_one("#status-bar", StatusBar)
            assert status._mode == "Form"
            app.switch_mode_to("Chat")
            assert status._mode == "Chat"

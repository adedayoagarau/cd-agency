"""Tests for the MemoryPanel widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.memory import MemoryEntry, ProjectMemory
from runtime.tui.widgets.memory_panel import MemoryPanel


class MemoryTestApp(App):
    def compose(self) -> ComposeResult:
        yield MemoryPanel(id="memory")


def _make_memory() -> ProjectMemory:
    memory = ProjectMemory()
    memory.entries["brand_voice"] = MemoryEntry(
        key="brand_voice",
        value="Warm, professional, clear",
        category="voice",
        source_agent="tone-evaluation-agent",
    )
    memory.entries["workspace_term"] = MemoryEntry(
        key="workspace_term",
        value="Use 'workspace' not 'project'",
        category="terminology",
        source_agent="content-consistency-checker",
    )
    return memory


class TestMemoryPanel:
    @pytest.mark.asyncio
    async def test_mounts(self):
        app = MemoryTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#memory", MemoryPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_set_memory(self):
        app = MemoryTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#memory", MemoryPanel)
            memory = _make_memory()
            panel.set_memory(memory)
            assert panel._memory is memory

    @pytest.mark.asyncio
    async def test_hidden_by_default(self):
        app = MemoryTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#memory", MemoryPanel)
            assert panel.display is False

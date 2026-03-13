"""Tests for the ContentEditor widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.tui.widgets.content_editor import ContentEditor


class EditorTestApp(App):
    def compose(self) -> ComposeResult:
        yield ContentEditor(initial_content="Initial text", id="editor")


class TestContentEditor:
    @pytest.mark.asyncio
    async def test_initial_content(self):
        app = EditorTestApp()
        async with app.run_test() as pilot:
            editor = app.query_one("#editor", ContentEditor)
            assert editor.text == "Initial text"

    @pytest.mark.asyncio
    async def test_set_text(self):
        app = EditorTestApp()
        async with app.run_test() as pilot:
            editor = app.query_one("#editor", ContentEditor)
            editor.text = "New content"
            assert editor.text == "New content"

    @pytest.mark.asyncio
    async def test_empty_initial(self):
        class EmptyApp(App):
            def compose(self) -> ComposeResult:
                yield ContentEditor(id="editor")
        app = EmptyApp()
        async with app.run_test() as pilot:
            editor = app.query_one("#editor", ContentEditor)
            assert editor.text == ""

"""Tests for the ScoringPanel widget."""

from __future__ import annotations

import pytest

from textual.app import App, ComposeResult

from runtime.tui.widgets.scoring_panel import ScoringPanel


class ScoringTestApp(App):
    def compose(self) -> ComposeResult:
        yield ScoringPanel(id="scoring")


class TestScoringPanel:
    @pytest.mark.asyncio
    async def test_mounts(self):
        app = ScoringTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#scoring", ScoringPanel)
            assert panel is not None

    @pytest.mark.asyncio
    async def test_update_scores_with_text(self):
        app = ScoringTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#scoring", ScoringPanel)
            panel.update_scores("This is a simple test sentence for readability.")
            # Should not raise — scores are rendered

    @pytest.mark.asyncio
    async def test_update_scores_empty_text(self):
        app = ScoringTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#scoring", ScoringPanel)
            panel.update_scores("")
            # Should not raise — clears the display

    @pytest.mark.asyncio
    async def test_update_scores_whitespace(self):
        app = ScoringTestApp()
        async with app.run_test() as pilot:
            panel = app.query_one("#scoring", ScoringPanel)
            panel.update_scores("   ")
            # Whitespace-only should be treated as empty

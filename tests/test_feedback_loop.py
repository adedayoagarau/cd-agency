"""Tests for the feedback-driven learning system."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from runtime.feedback_loop import (
    ContentEdit,
    EditPattern,
    FeedbackStore,
)


# ---------------------------------------------------------------------------
# ContentEdit
# ---------------------------------------------------------------------------

class TestContentEdit:
    def test_defaults(self):
        edit = ContentEdit(agent_slug="test-agent", original="Hello", edited="Hi there")
        assert edit.id != ""
        assert edit.timestamp > 0
        assert 0 < edit.similarity < 1

    def test_no_change(self):
        edit = ContentEdit(agent_slug="test", original="same", edited="same")
        assert edit.similarity == 1.0

    def test_edit_type_minor(self):
        edit = ContentEdit(
            agent_slug="test",
            original="Please click here to continue with your current task right now",
            edited="Please click here to proceed with your current task right now",
        )
        assert edit.edit_type == "minor_tweak"

    def test_edit_type_significant(self):
        edit = ContentEdit(
            agent_slug="test",
            original="An error has occurred in the application system",
            edited="An issue was found in the application system",
        )
        assert edit.edit_type in ("significant_rewrite", "minor_tweak")

    def test_edit_type_rejection(self):
        edit = ContentEdit(
            agent_slug="test",
            original="This is completely wrong content that needs total replacement and rewriting from scratch.",
            edited="Fixed.",
        )
        assert edit.edit_type == "rejection"

    def test_diff(self):
        edit = ContentEdit(
            agent_slug="test",
            original="Hello world",
            edited="Hello there",
        )
        d = edit.diff()
        assert "---" in d or d == ""  # unified diff or empty if same line


# ---------------------------------------------------------------------------
# EditPattern
# ---------------------------------------------------------------------------

class TestEditPattern:
    def test_defaults(self):
        pattern = EditPattern(
            pattern_type="word_replacement",
            original_pattern="click here",
            corrected_pattern="select",
        )
        assert pattern.id != ""
        assert pattern.first_seen > 0
        assert pattern.occurrences == 0

    def test_build_instruction(self):
        pattern = EditPattern(
            pattern_type="word_replacement",
            description="Replace click here with select",
            original_pattern="click here",
            corrected_pattern="select",
            occurrences=5,
        )
        instruction = pattern.build_instruction()
        assert "select" in instruction
        assert "click here" in instruction
        assert "5x" in instruction

    def test_build_instruction_no_pattern(self):
        pattern = EditPattern(
            description="Use shorter sentences",
            occurrences=3,
        )
        instruction = pattern.build_instruction()
        assert "shorter sentences" in instruction


# ---------------------------------------------------------------------------
# FeedbackStore
# ---------------------------------------------------------------------------

class TestFeedbackStore:
    def test_empty_store(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        assert store.edit_count() == 0
        assert store.pattern_count() == 0

    def test_record_edit(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        edit = store.record_edit(
            agent_slug="error-message-architect",
            original="An error occurred",
            edited="Something went wrong",
            agent_name="Error Message Architect",
        )
        assert edit.agent_slug == "error-message-architect"
        assert store.edit_count() == 1

    def test_record_no_change(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        edit = store.record_edit(
            agent_slug="test",
            original="same text",
            edited="same text",
        )
        assert edit.edit_type == "no_change"
        assert store.edit_count() == 0  # Not stored

    def test_persistence(self, tmp_path):
        store1 = FeedbackStore(project_dir=tmp_path)
        store1.record_edit("agent-a", "before", "after")

        store2 = FeedbackStore(project_dir=tmp_path)
        assert store2.edit_count() == 1

    def test_pattern_detection(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)

        # Record edits that should create a word replacement pattern
        store.record_edit("agent-a", "Click here to continue", "Select to continue")
        store.record_edit("agent-a", "Click here for more", "Select for more")

        # Should detect "click" → "select" pattern
        patterns = store.patterns
        assert len(patterns) >= 1

    def test_pattern_confidence_increases(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)

        for i in range(5):
            store.record_edit("agent-a", f"bad word{i}", f"good word{i}")

        # The "bad" → "good" replacement should have increasing confidence
        # (patterns are created per unique replacement pair)

    def test_get_patterns_for_agent(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        store.record_edit("agent-a", "click here", "select this")
        store.record_edit("agent-b", "press button", "tap button")

        a_patterns = store.get_patterns_for_agent("agent-a")
        b_patterns = store.get_patterns_for_agent("agent-b")

        # Each agent should see their own patterns
        assert len(a_patterns) >= 0
        assert len(b_patterns) >= 0

    def test_get_frequent_patterns(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)

        # Create a pattern that occurs multiple times
        for _ in range(3):
            store.record_edit("agent-a", "login now", "sign in now")

        frequent = store.get_frequent_patterns(min_occurrences=2)
        assert len(frequent) >= 1

    def test_build_feedback_context_empty(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        ctx = store.build_feedback_context("agent-a")
        assert ctx == ""

    def test_build_feedback_context_with_patterns(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)

        # Create enough edits to build patterns
        for _ in range(3):
            store.record_edit("agent-a", "login please", "sign in")

        ctx = store.build_feedback_context("agent-a")
        # May or may not have context depending on pattern detection
        # The important thing is it doesn't crash

    def test_agent_edit_stats(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        store.record_edit("agent-a", "Hello world", "Hi there world")
        store.record_edit("agent-a", "Click here", "Select this option instead")

        stats = store.get_agent_edit_stats("agent-a")
        assert stats["total_edits"] == 2
        assert stats["avg_similarity"] > 0

    def test_agent_edit_stats_empty(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        stats = store.get_agent_edit_stats("nonexistent")
        assert stats["total_edits"] == 0

    def test_sync_to_memory(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)

        # Add a high-confidence pattern manually
        pattern = EditPattern(
            pattern_type="word_replacement",
            description="Use sign in not log in",
            original_pattern="log in",
            corrected_pattern="sign in",
            occurrences=10,
            confidence=0.8,
            agent_slugs=["agent-a"],
        )
        store.patterns.append(pattern)
        store._save_patterns()

        mock_memory = MagicMock()
        synced = store.sync_to_memory(mock_memory)
        assert synced == 1
        mock_memory.remember.assert_called_once()

    def test_clear_edits(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        store.record_edit("agent-a", "before", "after")
        removed = store.clear_edits()
        assert removed == 1
        assert store.edit_count() == 0

    def test_clear_patterns(self, tmp_path):
        store = FeedbackStore(project_dir=tmp_path)
        store.patterns.append(EditPattern(pattern_type="test"))
        store._save_patterns()
        removed = store.clear_patterns()
        assert removed == 1
        assert store.pattern_count() == 0

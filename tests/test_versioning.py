"""Tests for the content versioning module."""

import pytest
from pathlib import Path

from runtime.versioning import ContentVersion, ContentHistory, MAX_VERSIONS


@pytest.fixture
def history(tmp_path: Path) -> ContentHistory:
    return ContentHistory(project_dir=tmp_path)


class TestContentVersion:
    def test_input_preview_short(self):
        v = ContentVersion(
            id="abc123", timestamp=0, agent_name="Test",
            agent_slug="test", input_text="Short", output_text="Out",
        )
        assert v.input_preview == "Short"

    def test_input_preview_long(self):
        v = ContentVersion(
            id="abc123", timestamp=0, agent_name="Test",
            agent_slug="test", input_text="x" * 100, output_text="Out",
        )
        assert v.input_preview.endswith("...")
        assert len(v.input_preview) == 83  # 80 + "..."

    def test_to_dict(self):
        v = ContentVersion(
            id="abc", timestamp=1.0, agent_name="Agent",
            agent_slug="agent", input_text="in", output_text="out",
            model="claude-3", tags=["test"],
        )
        d = v.to_dict()
        assert d["id"] == "abc"
        assert d["agent_slug"] == "agent"
        assert d["tags"] == ["test"]


class TestContentHistory:
    def test_record_and_get(self, history: ContentHistory):
        v = history.record(
            agent_name="Error Architect",
            agent_slug="error",
            input_text="Payment failed",
            output_text="We couldn't process your payment.",
            model="claude-3",
        )
        assert v.id
        assert v.agent_slug == "error"
        assert history.count == 1

        retrieved = history.get(v.id)
        assert retrieved is not None
        assert retrieved.input_text == "Payment failed"

    def test_list_recent(self, history: ContentHistory):
        for i in range(5):
            history.record(
                agent_name="Agent", agent_slug="agent",
                input_text=f"input-{i}", output_text=f"output-{i}",
            )
        recent = history.list_recent(3)
        assert len(recent) == 3
        # Most recent first
        assert recent[0].input_text == "input-4"

    def test_list_by_agent(self, history: ContentHistory):
        history.record(agent_name="A", agent_slug="a", input_text="1", output_text="1")
        history.record(agent_name="B", agent_slug="b", input_text="2", output_text="2")
        history.record(agent_name="A", agent_slug="a", input_text="3", output_text="3")

        a_versions = history.list_by_agent("a")
        assert len(a_versions) == 2
        b_versions = history.list_by_agent("b")
        assert len(b_versions) == 1

    def test_search(self, history: ContentHistory):
        history.record(agent_name="A", agent_slug="a",
                       input_text="payment error", output_text="fix payment")
        history.record(agent_name="B", agent_slug="b",
                       input_text="login flow", output_text="welcome back")

        results = history.search("payment")
        assert len(results) == 1
        assert results[0].agent_slug == "a"

    def test_diff(self, history: ContentHistory):
        v = history.record(
            agent_name="Agent", agent_slug="agent",
            input_text="Click here", output_text="View details",
        )
        d = history.diff(v.id)
        assert d is not None
        assert d["before"] == "Click here"
        assert d["after"] == "View details"
        assert d["char_delta"] == len("View details") - len("Click here")

    def test_diff_not_found(self, history: ContentHistory):
        assert history.diff("nonexistent") is None

    def test_clear(self, history: ContentHistory):
        history.record(agent_name="A", agent_slug="a", input_text="1", output_text="1")
        history.record(agent_name="B", agent_slug="b", input_text="2", output_text="2")
        assert history.count == 2
        count = history.clear()
        assert count == 2
        assert history.count == 0

    def test_persistence(self, tmp_path: Path):
        # Save
        h1 = ContentHistory(project_dir=tmp_path)
        h1.record(agent_name="A", agent_slug="a", input_text="hello", output_text="world")
        assert h1.count == 1

        # Reload
        h2 = ContentHistory.load(project_dir=tmp_path)
        assert h2.count == 1
        assert h2.versions[0].input_text == "hello"

    def test_max_versions_trimmed(self, history: ContentHistory):
        for i in range(MAX_VERSIONS + 50):
            history.record(
                agent_name="Agent", agent_slug="agent",
                input_text=f"in-{i}", output_text=f"out-{i}",
            )
        # After save, should be trimmed to MAX_VERSIONS
        reloaded = ContentHistory.load(project_dir=history.project_dir)
        assert reloaded.count == MAX_VERSIONS
        # Most recent entries should be kept
        assert reloaded.versions[-1].input_text == f"in-{MAX_VERSIONS + 49}"

    def test_summary_empty(self, history: ContentHistory):
        s = history.summary()
        assert s["count"] == 0
        assert s["latest"] is None

    def test_summary_with_data(self, history: ContentHistory):
        history.record(agent_name="Error", agent_slug="error",
                       input_text="test", output_text="result")
        s = history.summary()
        assert s["count"] == 1
        assert "error" in s["agents_used"]
        assert s["latest"]["agent"] == "Error"

    def test_record_with_fields(self, history: ContentHistory):
        v = history.record(
            agent_name="A", agent_slug="a",
            input_text="test", output_text="result",
            input_fields={"severity": "critical", "platform": "ios"},
            tags=["test", "mobile"],
            notes="Testing mobile variant",
        )
        assert v.input_fields["severity"] == "critical"
        assert v.tags == ["test", "mobile"]
        assert v.notes == "Testing mobile variant"

    def test_unique_ids(self, history: ContentHistory):
        v1 = history.record(agent_name="A", agent_slug="a", input_text="a", output_text="b")
        v2 = history.record(agent_name="A", agent_slug="a", input_text="c", output_text="d")
        assert v1.id != v2.id

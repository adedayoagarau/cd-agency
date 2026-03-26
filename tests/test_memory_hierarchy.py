"""Tests for MemoryHierarchy — session > project > workspace resolution."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.memory import MemoryEntry, ProjectMemory
from runtime.memory_hierarchy import MemoryHierarchy
from runtime.workspace_memory import WorkspaceMemory


@pytest.fixture
def hierarchy(tmp_path):
    """Create a MemoryHierarchy using tmp directories."""
    ws_path = tmp_path / "workspace" / "test"

    with patch("runtime.workspace_memory.WORKSPACE_ROOT", tmp_path / "workspace"):
        with patch("runtime.session_memory._WORKSPACE_SESSIONS_DIR", tmp_path / "workspace" / "sessions"):
            h = MemoryHierarchy(
                project_dir=tmp_path,
                workspace_id="test",
            )
    return h


class TestMemoryHierarchyWrite:
    def test_remember_project(self, hierarchy):
        hierarchy.remember("key1", "value1", visibility="project")
        assert hierarchy.project.recall("key1") is not None
        assert hierarchy.workspace.recall("key1") is None

    def test_remember_workspace(self, hierarchy):
        hierarchy.remember("key1", "value1", visibility="workspace")
        assert hierarchy.project.recall("key1") is not None
        assert hierarchy.workspace.recall("key1") is not None

    def test_remember_session(self, hierarchy):
        hierarchy.remember("key1", "value1", visibility="session")
        # Session-only: not stored in project or workspace
        assert hierarchy.project.recall("key1") is None
        assert hierarchy.workspace.recall("key1") is None
        # But tracked in session topics
        assert any("key1" in t for t in hierarchy.session.context.active_topics)

    def test_workspace_entry_has_source_project(self, hierarchy):
        hierarchy.remember("key1", "value1", visibility="workspace")
        entry = hierarchy.workspace.recall("key1")
        assert "source_project" in entry.metadata


class TestMemoryHierarchyRead:
    def test_recall_project_takes_precedence(self, hierarchy):
        hierarchy.project.remember("key1", "project-value")
        hierarchy.workspace.remember("key1", "workspace-value")
        entry = hierarchy.recall("key1")
        assert entry.value == "project-value"

    def test_recall_falls_back_to_workspace(self, hierarchy):
        hierarchy.workspace.remember("key1", "workspace-value")
        entry = hierarchy.recall("key1")
        assert entry.value == "workspace-value"

    def test_recall_missing(self, hierarchy):
        assert hierarchy.recall("nonexistent") is None

    def test_recall_by_category_merges(self, hierarchy):
        hierarchy.project.remember("p1", "v1", category="terminology")
        hierarchy.workspace.remember("w1", "v2", category="terminology")
        entries = hierarchy.recall_by_category("terminology")
        assert len(entries) == 2

    def test_recall_by_category_deduplicates(self, hierarchy):
        hierarchy.project.remember("same-key", "project-val", category="terminology")
        hierarchy.workspace.remember("same-key", "workspace-val", category="terminology")
        entries = hierarchy.recall_by_category("terminology")
        # Project wins, workspace duplicate excluded
        assert len(entries) == 1
        assert entries[0].value == "project-val"

    def test_search_project_first(self, hierarchy):
        hierarchy.project.remember("test-key", "project result about search")
        hierarchy.workspace.remember("test-key-ws", "workspace result about search")
        results = hierarchy.search("search")
        assert len(results) == 2
        assert results[0].value == "project result about search"

    def test_search_deduplicates(self, hierarchy):
        hierarchy.project.remember("shared", "value about testing")
        hierarchy.workspace.remember("shared", "different value about testing")
        results = hierarchy.search("testing")
        assert len(results) == 1  # Workspace duplicate excluded


class TestMemoryHierarchyContext:
    def test_get_context_empty(self, hierarchy):
        ctx = hierarchy.get_context_for_agent("test-agent")
        assert ctx == ""

    def test_get_context_project_only(self, hierarchy):
        hierarchy.project.remember("tone", "friendly", category="voice")
        ctx = hierarchy.get_context_for_agent("test-agent")
        assert "friendly" in ctx

    def test_get_context_includes_workspace(self, hierarchy):
        hierarchy.workspace.remember("ws-term", "Use 'sign in'", category="terminology")
        ctx = hierarchy.get_context_for_agent("test-agent", query="sign")
        assert "sign in" in ctx
        assert "Workspace Memory" in ctx

    def test_get_context_project_overrides_workspace(self, hierarchy):
        hierarchy.project.remember("login-term", "Use 'sign in'", category="terminology")
        hierarchy.workspace.remember("login-term", "Use 'log in'", category="terminology")
        ctx = hierarchy.get_context_for_agent("test-agent")
        # Workspace entry for same key should be excluded
        assert "sign in" in ctx
        # The workspace "log in" should not appear since project overrides
        assert "Workspace Memory" not in ctx or "log in" not in ctx

    def test_get_context_updates_session(self, hierarchy):
        hierarchy.project.remember("k1", "v1", category="decision")
        hierarchy.get_context_for_agent("My Agent")
        assert "agent:My Agent" in hierarchy.session.context.active_topics


class TestPromotionAndSync:
    def test_promote_to_workspace(self, hierarchy):
        hierarchy.project.remember("key1", "value1", category="terminology")
        assert hierarchy.promote_to_workspace("key1") is True
        assert hierarchy.workspace.recall("key1") is not None

    def test_promote_nonexistent(self, hierarchy):
        assert hierarchy.promote_to_workspace("nonexistent") is False

    def test_sync_to_workspace(self, hierarchy):
        hierarchy.project.remember(
            "term1", "v1", category="terminology",
            metadata={"visibility": "workspace"},
        )
        hierarchy.project.remember(
            "brand1", "v2", category="brand_dna",
        )
        hierarchy.project.remember(
            "decision1", "v3", category="decision",
        )
        count = hierarchy.sync_to_workspace()
        # terminology with visibility=workspace + brand_dna auto-syncs
        assert count >= 2
        assert hierarchy.workspace.recall("term1") is not None
        assert hierarchy.workspace.recall("brand1") is not None


class TestPruning:
    def test_prune_old_entries(self, hierarchy):
        # Add an old entry
        old_entry = MemoryEntry(
            key="old", value="old value", category="decision",
            timestamp=time.time() - (100 * 24 * 3600),  # 100 days old
        )
        hierarchy.project.entries["old"] = old_entry
        hierarchy.project.save()

        # Add a recent entry
        hierarchy.project.remember("recent", "recent value")

        result = hierarchy.prune(max_age_days=90)
        assert result["project"] == 1
        assert hierarchy.project.recall("old") is None
        assert hierarchy.project.recall("recent") is not None

    def test_prune_dry_run(self, hierarchy):
        old_entry = MemoryEntry(
            key="old", value="old value", category="decision",
            timestamp=time.time() - (100 * 24 * 3600),
        )
        hierarchy.project.entries["old"] = old_entry
        hierarchy.project.save()

        result = hierarchy.prune(max_age_days=90, dry_run=True)
        assert result["project"] == 1
        # Dry run — entry still exists
        assert hierarchy.project.recall("old") is not None


class TestExportImport:
    def test_export_all(self, hierarchy):
        hierarchy.project.remember("pk1", "pv1")
        hierarchy.workspace.remember("wk1", "wv1")
        export = hierarchy.export_all()
        assert "session" in export
        assert "project" in export
        assert "workspace" in export
        assert export["project"]["entry_count"] == 1
        assert export["workspace"]["entry_count"] == 1

    def test_import_project(self, hierarchy):
        data = {
            "entries": {
                "imported-key": {
                    "key": "imported-key",
                    "value": "imported-value",
                    "category": "terminology",
                    "source_agent": "",
                    "timestamp": time.time(),
                    "metadata": {},
                }
            }
        }
        count = hierarchy.import_memory(data, target="project")
        assert count == 1
        assert hierarchy.project.recall("imported-key").value == "imported-value"

    def test_import_dedup_newer_wins(self, hierarchy):
        hierarchy.project.remember("key1", "old-value")
        data = {
            "entries": {
                "key1": {
                    "key": "key1",
                    "value": "newer-value",
                    "category": "decision",
                    "source_agent": "",
                    "timestamp": time.time() + 100,  # Newer
                    "metadata": {},
                }
            }
        }
        count = hierarchy.import_memory(data, target="project")
        assert count == 1
        assert hierarchy.project.recall("key1").value == "newer-value"

    def test_import_dedup_older_skipped(self, hierarchy):
        hierarchy.project.remember("key1", "current-value")
        data = {
            "entries": {
                "key1": {
                    "key": "key1",
                    "value": "older-value",
                    "category": "decision",
                    "source_agent": "",
                    "timestamp": 1000,  # Very old
                    "metadata": {},
                }
            }
        }
        count = hierarchy.import_memory(data, target="project")
        assert count == 0
        assert hierarchy.project.recall("key1").value == "current-value"


class TestBackwardCompatibility:
    def test_project_memory_api_unchanged(self, tmp_path):
        """ProjectMemory should work exactly as before, even within hierarchy."""
        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("k1", "v1", category="terminology")
        mem.remember("k2", "v2", category="voice")

        # All existing methods work
        assert mem.recall("k1").value == "v1"
        assert len(mem.recall_by_category("terminology")) == 1
        results = mem.search("v1")
        assert len(results) == 1
        ctx = mem.get_context_for_agent()
        assert "v1" in ctx
        assert mem.forget("k1") is True
        assert len(mem) == 1

    def test_hierarchy_len(self, hierarchy):
        hierarchy.project.remember("p1", "v1")
        hierarchy.workspace.remember("w1", "v2")
        assert len(hierarchy) == 2


# ---------------------------------------------------------------------------
# Integration: runner uses MemoryHierarchy
# ---------------------------------------------------------------------------

class TestRunnerIntegration:
    @patch("runtime.runner.ModelRouter.from_config")
    def test_runner_uses_hierarchy(self, mock_from_config):
        from runtime.agent import Agent, AgentInput
        from runtime.config import Config
        from runtime.model_providers import ProviderResponse
        from runtime.runner import AgentRunner

        mock_provider = MagicMock()
        mock_provider.complete.return_value = ProviderResponse(
            content="Response", input_tokens=10, output_tokens=5,
        )
        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        agent = Agent(
            name="Test",
            description="Test",
            inputs=[AgentInput(name="content", type="string", required=True)],
            system_prompt="You are a test agent.",
            source_file="test.md",
        )
        config = Config(api_key="test-key", model="test-model")
        runner = AgentRunner(config)

        # Should not crash — MemoryHierarchy is now used
        result = runner.run(agent, {"content": "test"})
        assert result.content == "Response"


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

class TestCLIMemoryCommands:
    def test_memory_promote_command(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["memory", "promote", "nonexistent-key"])
        assert result.exit_code == 0
        assert "not found" in result.output.lower()

    def test_memory_prune_dry_run(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["memory", "prune", "--dry-run"])
        assert result.exit_code == 0

    def test_session_list_command(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["session", "list"])
        assert result.exit_code == 0

    def test_session_cleanup_command(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["session", "cleanup"])
        assert result.exit_code == 0

    def test_workspace_status_command(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["workspace", "status"])
        assert result.exit_code == 0

    def test_workspace_sync_command(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["workspace", "sync"])
        assert result.exit_code == 0

    def test_workspace_show_empty(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["workspace", "show"])
        assert result.exit_code == 0

"""Tests for vector-based semantic memory.

These tests require ``chromadb`` and ``sentence-transformers`` with a
working embedding model.  They are automatically skipped when those
packages are not installed or the model cannot be downloaded, so the
rest of the test suite (541 tests) remains unaffected.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path

# Skip entire module if dependencies are missing
chromadb = pytest.importorskip("chromadb", reason="chromadb not installed")
pytest.importorskip("sentence_transformers", reason="sentence-transformers not installed")

from runtime.vector_memory import VectorMemory, migrate_json_to_vectors, COLLECTION_NAME
from runtime.memory import ProjectMemory, MemoryEntry, MEMORY_DIR


def _model_available() -> bool:
    """Return True if the embedding model can be loaded and encode text."""
    try:
        vm = VectorMemory(project_dir=Path("/tmp/_vector_memory_probe"))
        vm._get_model()
        return True
    except Exception:
        return False


_HAS_MODEL = _model_available()
requires_model = pytest.mark.skipif(
    not _HAS_MODEL,
    reason="Embedding model not available (no internet or download failed)",
)


@pytest.fixture
def vmem(tmp_path: Path) -> VectorMemory:
    """Fresh VectorMemory backed by a temp directory."""
    return VectorMemory(project_dir=tmp_path)


@pytest.fixture
def populated_vmem(vmem: VectorMemory) -> VectorMemory:
    """VectorMemory pre-loaded with diverse entries for search tests."""
    vmem.remember(
        "button_labels",
        "Use 'Save' instead of 'Submit' for form actions that persist data",
        category="terminology",
        source_agent="microcopy",
    )
    vmem.remember(
        "error_tone",
        "Error messages should be empathetic, never blame the user, and suggest a fix",
        category="voice",
        source_agent="error-message",
    )
    vmem.remember(
        "onboarding_length",
        "Keep onboarding flows under 4 steps. Users abandon after step 3",
        category="pattern",
        source_agent="onboarding",
    )
    vmem.remember(
        "date_format",
        "Always use ISO 8601 date format (YYYY-MM-DD) in technical contexts",
        category="terminology",
        source_agent="microcopy",
    )
    vmem.remember(
        "cta_wording",
        "Call-to-action buttons should start with a verb: Get, Start, Try, Join",
        category="pattern",
        source_agent="cta",
    )
    return vmem


# ------------------------------------------------------------------
# Core CRUD
# ------------------------------------------------------------------


@requires_model
class TestRememberAndRecall:
    def test_remember_stores_entry(self, vmem: VectorMemory) -> None:
        vmem.remember("test_key", "test_value", category="decision", source_agent="agent-a")
        entry = vmem.recall("test_key")
        assert entry is not None
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.category == "decision"
        assert entry.source_agent == "agent-a"
        assert entry.timestamp > 0

    def test_recall_missing_key(self, vmem: VectorMemory) -> None:
        assert vmem.recall("nonexistent") is None

    def test_remember_upserts(self, vmem: VectorMemory) -> None:
        vmem.remember("k", "original")
        vmem.remember("k", "updated")
        entry = vmem.recall("k")
        assert entry is not None
        assert entry.value == "updated"
        assert vmem.count() == 1

    def test_remember_with_metadata(self, vmem: VectorMemory) -> None:
        vmem.remember("k", "v", metadata={"priority": "high", "count": 3})
        entry = vmem.recall("k")
        assert entry is not None
        assert entry.metadata.get("priority") == "high"
        assert entry.metadata.get("count") == 3

    def test_count(self, vmem: VectorMemory) -> None:
        assert vmem.count() == 0
        vmem.remember("a", "1")
        vmem.remember("b", "2")
        assert vmem.count() == 2


# ------------------------------------------------------------------
# Semantic search
# ------------------------------------------------------------------


@requires_model
class TestSemanticSearch:
    def test_search_returns_relevant_results(self, populated_vmem: VectorMemory) -> None:
        """'handling user errors gracefully' should rank the error_tone entry highest."""
        results = populated_vmem.semantic_search("handling user errors gracefully")
        assert len(results) > 0
        # The error_tone entry should be in the top results
        keys = [r.key for r in results]
        assert "error_tone" in keys
        # It should be the most relevant (first) result
        assert results[0].key == "error_tone"

    def test_search_button_related(self, populated_vmem: VectorMemory) -> None:
        """Searching for button-related content should surface button/CTA entries."""
        results = populated_vmem.semantic_search("what text to put on buttons")
        keys = [r.key for r in results]
        assert "button_labels" in keys or "cta_wording" in keys

    def test_search_respects_n_results(self, populated_vmem: VectorMemory) -> None:
        results = populated_vmem.semantic_search("content design", n_results=2)
        assert len(results) <= 2

    def test_search_empty_collection(self, vmem: VectorMemory) -> None:
        results = vmem.semantic_search("anything")
        assert results == []

    def test_search_single_entry(self, vmem: VectorMemory) -> None:
        vmem.remember("only", "the sole entry in the store")
        results = vmem.semantic_search("entry")
        assert len(results) == 1
        assert results[0].key == "only"


# ------------------------------------------------------------------
# Category filtering
# ------------------------------------------------------------------


@requires_model
class TestRecallByCategory:
    def test_filter_terminology(self, populated_vmem: VectorMemory) -> None:
        terms = populated_vmem.recall_by_category("terminology")
        assert len(terms) == 2
        keys = {e.key for e in terms}
        assert keys == {"button_labels", "date_format"}

    def test_filter_voice(self, populated_vmem: VectorMemory) -> None:
        voice = populated_vmem.recall_by_category("voice")
        assert len(voice) == 1
        assert voice[0].key == "error_tone"

    def test_filter_empty_category(self, populated_vmem: VectorMemory) -> None:
        assert populated_vmem.recall_by_category("nonexistent") == []


# ------------------------------------------------------------------
# Forget
# ------------------------------------------------------------------


@requires_model
class TestForget:
    def test_forget_existing(self, vmem: VectorMemory) -> None:
        vmem.remember("k", "v")
        assert vmem.forget("k") is True
        assert vmem.recall("k") is None
        assert vmem.count() == 0

    def test_forget_nonexistent(self, vmem: VectorMemory) -> None:
        assert vmem.forget("nope") is False


# ------------------------------------------------------------------
# Context for agent
# ------------------------------------------------------------------


@requires_model
class TestGetContextForAgent:
    def test_with_query(self, populated_vmem: VectorMemory) -> None:
        ctx = populated_vmem.get_context_for_agent(query="error messages")
        assert "error_tone" in ctx or "empathetic" in ctx
        assert "Project Memory" in ctx

    def test_without_query_returns_all(self, populated_vmem: VectorMemory) -> None:
        ctx = populated_vmem.get_context_for_agent()
        # Should contain entries from all categories
        assert "button_labels" in ctx or "Save" in ctx
        assert "error_tone" in ctx or "empathetic" in ctx

    def test_empty_collection(self, vmem: VectorMemory) -> None:
        assert vmem.get_context_for_agent(query="anything") == ""


# ------------------------------------------------------------------
# Migration from JSON
# ------------------------------------------------------------------


@requires_model
class TestMigration:
    def test_migrate_json_to_vectors(self, tmp_path: Path) -> None:
        # Write a legacy memory.json
        memory_dir = tmp_path / MEMORY_DIR
        memory_dir.mkdir()
        legacy_data = {
            "version": "1.0",
            "entries": {
                "term_workspace": {
                    "key": "term_workspace",
                    "value": "Use 'workspace' not 'project'",
                    "category": "terminology",
                    "source_agent": "microcopy",
                    "timestamp": 1700000000.0,
                    "metadata": {},
                },
                "tone_friendly": {
                    "key": "tone_friendly",
                    "value": "Keep tone friendly but professional",
                    "category": "voice",
                    "source_agent": "tone",
                    "timestamp": 1700000001.0,
                    "metadata": {},
                },
                "pattern_short": {
                    "key": "pattern_short",
                    "value": "Sentences under 20 words",
                    "category": "pattern",
                    "source_agent": "readability",
                    "timestamp": 1700000002.0,
                    "metadata": {},
                },
            },
        }
        (memory_dir / "memory.json").write_text(
            json.dumps(legacy_data), encoding="utf-8"
        )

        count = migrate_json_to_vectors(tmp_path)
        assert count == 3

        # Verify entries are in ChromaDB
        vmem = VectorMemory(project_dir=tmp_path)
        assert vmem.count() == 3

        entry = vmem.recall("term_workspace")
        assert entry is not None
        assert entry.value == "Use 'workspace' not 'project'"
        assert entry.category == "terminology"

    def test_migrate_no_json(self, tmp_path: Path) -> None:
        assert migrate_json_to_vectors(tmp_path) == 0

    def test_migrate_empty_json(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / MEMORY_DIR
        memory_dir.mkdir()
        (memory_dir / "memory.json").write_text(
            json.dumps({"version": "1.0", "entries": {}}), encoding="utf-8"
        )
        assert migrate_json_to_vectors(tmp_path) == 0

    def test_migrate_idempotent(self, tmp_path: Path) -> None:
        memory_dir = tmp_path / MEMORY_DIR
        memory_dir.mkdir()
        legacy_data = {
            "version": "1.0",
            "entries": {
                "k1": {
                    "key": "k1",
                    "value": "v1",
                    "category": "decision",
                    "source_agent": "",
                    "timestamp": 1700000000.0,
                    "metadata": {},
                },
            },
        }
        (memory_dir / "memory.json").write_text(
            json.dumps(legacy_data), encoding="utf-8"
        )

        count1 = migrate_json_to_vectors(tmp_path)
        count2 = migrate_json_to_vectors(tmp_path)
        assert count1 == 1
        assert count2 == 1  # same count, but upserted — no duplicates

        vmem = VectorMemory(project_dir=tmp_path)
        assert vmem.count() == 1


# ------------------------------------------------------------------
# ProjectMemory integration (vector store as internal backend)
# ------------------------------------------------------------------


@requires_model
class TestProjectMemoryIntegration:
    def test_remember_syncs_to_vector_store(self, tmp_path: Path) -> None:
        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("sync_test", "value for sync", category="decision")

        # Verify it's in the JSON entries
        assert mem.recall("sync_test") is not None

        # Verify it's also in the vector store
        if mem.vector is not None:
            entry = mem.vector.recall("sync_test")
            assert entry is not None
            assert entry.value == "value for sync"

    def test_forget_removes_from_vector_store(self, tmp_path: Path) -> None:
        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("to_forget", "will be removed", category="decision")
        mem.forget("to_forget")

        assert mem.recall("to_forget") is None
        if mem.vector is not None:
            assert mem.vector.recall("to_forget") is None

    def test_search_uses_vector_store(self, tmp_path: Path) -> None:
        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember(
            "error_guidance",
            "Error messages should be helpful and suggest next steps",
            category="voice",
        )
        mem.remember(
            "button_text",
            "Use action verbs on buttons like Save, Submit, Continue",
            category="terminology",
        )

        if mem.vector is not None:
            results = mem.search("how to write good error messages")
            assert len(results) > 0
            # Semantic search should rank error_guidance above button_text
            assert results[0].key == "error_guidance"

    def test_get_context_with_query(self, tmp_path: Path) -> None:
        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("onb", "Onboarding should be under 3 steps", category="pattern")
        mem.remember("err", "Errors need recovery actions", category="voice")

        ctx = mem.get_context_for_agent("test-agent", query="onboarding design")
        if mem.vector is not None:
            # Semantic path should return relevant results
            assert ctx != ""
            assert "onb" in ctx.lower() or "onboarding" in ctx.lower()

    def test_get_context_without_query_falls_back(self, tmp_path: Path) -> None:
        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("t1", "v1", category="terminology")
        ctx = mem.get_context_for_agent("test-agent")
        # Without query, uses category-based path
        assert "Terminology" in ctx

    def test_auto_migration_on_load(self, tmp_path: Path) -> None:
        # Create a JSON memory file
        memory_dir = tmp_path / MEMORY_DIR
        memory_dir.mkdir()
        legacy_data = {
            "version": "1.0",
            "entries": {
                "migrated_key": {
                    "key": "migrated_key",
                    "value": "should be auto-migrated",
                    "category": "decision",
                    "source_agent": "test",
                    "timestamp": 1700000000.0,
                    "metadata": {},
                },
            },
        }
        (memory_dir / "memory.json").write_text(
            json.dumps(legacy_data), encoding="utf-8"
        )

        mem = ProjectMemory.load(tmp_path)
        assert len(mem) == 1

        # If vector store is available, it should have auto-migrated
        if mem.vector is not None:
            assert mem.vector.count() == 1
            entry = mem.vector.recall("migrated_key")
            assert entry is not None
            assert entry.value == "should be auto-migrated"

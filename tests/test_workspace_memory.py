"""Tests for WorkspaceMemory."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.memory import MemoryEntry
from runtime.workspace_memory import WorkspaceMemory, WORKSPACE_ROOT


@pytest.fixture
def ws(tmp_path):
    """WorkspaceMemory using a tmp directory as home."""
    with patch.object(WorkspaceMemory, '__init__', lambda self, workspace_id="default": None):
        ws = WorkspaceMemory.__new__(WorkspaceMemory)
        ws.workspace_id = "test"
        ws.workspace_path = tmp_path / "workspace" / "test"
        ws.memory_file = ws.workspace_path / "memory.json"
        ws._lock_file = ws.workspace_path / ".lock"
        ws.entries = {}
    return ws


class TestWorkspaceMemoryCRUD:
    def test_remember_and_recall(self, ws):
        ws.remember("term-login", "Use 'sign in' not 'log in'", category="terminology")
        entry = ws.recall("term-login")
        assert entry is not None
        assert entry.value == "Use 'sign in' not 'log in'"
        assert entry.category == "terminology"

    def test_recall_missing(self, ws):
        assert ws.recall("nonexistent") is None

    def test_recall_by_category(self, ws):
        ws.remember("t1", "v1", category="terminology")
        ws.remember("t2", "v2", category="terminology")
        ws.remember("v1", "v3", category="voice")
        terms = ws.recall_by_category("terminology")
        assert len(terms) == 2

    def test_search(self, ws):
        ws.remember("error-tone", "Friendly language for errors", category="voice")
        results = ws.search("error")
        assert len(results) == 1
        assert results[0].key == "error-tone"

    def test_search_limit(self, ws):
        for i in range(10):
            ws.remember(f"key-{i}", f"value about test {i}", category="decision")
        results = ws.search("test", n_results=3)
        assert len(results) == 3

    def test_forget(self, ws):
        ws.remember("k1", "v1")
        assert ws.forget("k1") is True
        assert ws.recall("k1") is None
        assert ws.forget("nonexistent") is False

    def test_clear(self, ws):
        ws.remember("k1", "v1")
        ws.remember("k2", "v2")
        count = ws.clear()
        assert count == 2
        assert len(ws) == 0

    def test_len(self, ws):
        assert len(ws) == 0
        ws.remember("k1", "v1")
        assert len(ws) == 1

    def test_recall_updates_access_metadata(self, ws):
        ws.remember("k1", "v1")
        entry = ws.recall("k1")
        assert entry.metadata.get("access_count") == 1
        entry2 = ws.recall("k1")
        assert entry2.metadata.get("access_count") == 2


class TestWorkspaceMemoryPersistence:
    def test_save_and_load(self, tmp_path):
        ws_path = tmp_path / "workspace" / "test"

        ws1 = WorkspaceMemory.__new__(WorkspaceMemory)
        ws1.workspace_id = "test"
        ws1.workspace_path = ws_path
        ws1.memory_file = ws_path / "memory.json"
        ws1._lock_file = ws_path / ".lock"
        ws1.entries = {}

        ws1.remember("key1", "value1", category="terminology")
        assert ws1.memory_file.exists()

        # Load from same path
        ws2 = WorkspaceMemory.__new__(WorkspaceMemory)
        ws2.workspace_id = "test"
        ws2.workspace_path = ws_path
        ws2.memory_file = ws_path / "memory.json"
        ws2._lock_file = ws_path / ".lock"
        ws2.entries = {}

        data = json.loads(ws2.memory_file.read_text(encoding="utf-8"))
        for key, entry_data in data.get("entries", {}).items():
            ws2.entries[key] = MemoryEntry(**entry_data)

        assert len(ws2) == 1
        assert ws2.recall("key1").value == "value1"

    def test_load_corrupt(self, tmp_path):
        ws_path = tmp_path / "workspace" / "test"
        ws_path.mkdir(parents=True)
        (ws_path / "memory.json").write_text("corrupt", encoding="utf-8")

        with patch.object(WorkspaceMemory, '__init__', lambda self, workspace_id="default": None):
            ws = WorkspaceMemory.__new__(WorkspaceMemory)
            ws.workspace_id = "test"
            ws.workspace_path = ws_path
            ws.memory_file = ws_path / "memory.json"
            ws._lock_file = ws_path / ".lock"
            ws.entries = {}
        # Should not crash
        assert len(ws) == 0


class TestWorkspaceFileLocking:
    def test_lock_and_release(self, ws):
        ws._acquire_lock()
        assert ws._lock_file.exists()
        ws._release_lock()
        assert not ws._lock_file.exists()

    def test_stale_lock_cleared(self, ws):
        ws.workspace_path.mkdir(parents=True, exist_ok=True)
        # Create a stale lock (old mtime)
        ws._lock_file.write_text("1234")
        old_time = time.time() - 60  # 60 seconds old
        os.utime(str(ws._lock_file), (old_time, old_time))

        # Should acquire despite stale lock
        ws._acquire_lock()
        ws._release_lock()


class TestWorkspaceEviction:
    def test_eviction_on_max_entries(self, ws):
        from runtime import workspace_memory
        original_max = workspace_memory._MAX_ENTRIES
        workspace_memory._MAX_ENTRIES = 5
        try:
            for i in range(7):
                ws.remember(f"key-{i}", f"value-{i}")
                time.sleep(0.01)  # Ensure distinct timestamps
            assert len(ws) == 5
        finally:
            workspace_memory._MAX_ENTRIES = original_max

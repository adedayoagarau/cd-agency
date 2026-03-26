"""Workspace-level memory — shared across projects in ~/.cd-agency/workspace/.

Workspace memory stores learnings that apply across projects (brand DNA,
cross-project terminology, shared voice decisions). It uses the same
MemoryEntry format as ProjectMemory for compatibility.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from runtime.memory import MemoryEntry

WORKSPACE_ROOT = Path.home() / ".cd-agency" / "workspace"
WORKSPACE_MEMORY_FILE = "memory.json"
_LOCK_TIMEOUT = 5.0  # seconds
_MAX_ENTRIES = 10_000


class WorkspaceMemory:
    """Cross-project memory store in the user's home directory.

    Uses file-based locking for safe concurrent access from multiple
    terminal sessions.
    """

    def __init__(self, workspace_id: str = "default") -> None:
        self.workspace_id = workspace_id
        self.workspace_path = WORKSPACE_ROOT / workspace_id
        self.memory_file = self.workspace_path / WORKSPACE_MEMORY_FILE
        self._lock_file = self.workspace_path / ".lock"
        self.entries: dict[str, MemoryEntry] = {}

    @classmethod
    def load(cls, workspace_id: str = "default") -> WorkspaceMemory:
        """Load workspace memory from disk."""
        ws = cls(workspace_id=workspace_id)
        if ws.memory_file.exists():
            try:
                data = json.loads(ws.memory_file.read_text(encoding="utf-8"))
                for key, entry_data in data.get("entries", {}).items():
                    ws.entries[key] = MemoryEntry(**entry_data)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass  # Corrupted file — start fresh
        return ws

    def save(self) -> None:
        """Persist to disk with file locking."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self._acquire_lock()
        try:
            data = {
                "version": "1.0",
                "workspace_id": self.workspace_id,
                "entries": {k: asdict(v) for k, v in self.entries.items()},
            }
            self.memory_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        finally:
            self._release_lock()

    def remember(
        self,
        key: str,
        value: str,
        category: str = "decision",
        source_agent: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a memory entry at workspace level."""
        meta = metadata or {}
        meta.setdefault("visibility", "workspace")

        self.entries[key] = MemoryEntry(
            key=key,
            value=value,
            category=category,
            source_agent=source_agent,
            metadata=meta,
        )

        # Enforce entry limit — evict oldest by timestamp
        if len(self.entries) > _MAX_ENTRIES:
            self._evict_oldest()

        self.save()

    def recall(self, key: str) -> MemoryEntry | None:
        """Retrieve a specific memory by key."""
        entry = self.entries.get(key)
        if entry:
            entry.metadata["last_accessed"] = time.time()
            entry.metadata["access_count"] = entry.metadata.get("access_count", 0) + 1
        return entry

    def recall_by_category(self, category: str) -> list[MemoryEntry]:
        """Get all memories in a category."""
        return [e for e in self.entries.values() if e.category == category]

    def search(self, query: str, n_results: int = 5) -> list[MemoryEntry]:
        """Search workspace memories by substring matching."""
        query_lower = query.lower()
        matches = [
            e for e in self.entries.values()
            if query_lower in e.key.lower() or query_lower in e.value.lower()
        ]
        return matches[:n_results]

    def forget(self, key: str) -> bool:
        """Remove a workspace memory entry."""
        if key in self.entries:
            del self.entries[key]
            self.save()
            return True
        return False

    def clear(self) -> int:
        """Clear all workspace memory."""
        count = len(self.entries)
        self.entries.clear()
        self.save()
        return count

    def _evict_oldest(self) -> None:
        """Remove oldest entries to stay under _MAX_ENTRIES."""
        sorted_keys = sorted(
            self.entries.keys(),
            key=lambda k: self.entries[k].timestamp,
        )
        while len(self.entries) > _MAX_ENTRIES:
            del self.entries[sorted_keys.pop(0)]

    def _acquire_lock(self) -> None:
        """Acquire a file lock (best-effort, with timeout)."""
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + _LOCK_TIMEOUT
        while time.monotonic() < deadline:
            try:
                fd = os.open(str(self._lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                return
            except FileExistsError:
                # Check for stale lock (older than 30s)
                try:
                    age = time.time() - self._lock_file.stat().st_mtime
                    if age > 30:
                        self._lock_file.unlink(missing_ok=True)
                        continue
                except OSError:
                    pass
                time.sleep(0.05)
        # Timeout — proceed without lock (best-effort)

    def _release_lock(self) -> None:
        """Release the file lock."""
        self._lock_file.unlink(missing_ok=True)

    def __len__(self) -> int:
        return len(self.entries)

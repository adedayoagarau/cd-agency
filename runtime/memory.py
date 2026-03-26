"""Project-level memory store for cross-session agent context.

Agents can read from memory ("Last time we decided to use 'workspace' not 'project'")
and write to memory after user confirms a choice. Memory is scoped per project directory.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


MEMORY_DIR = ".cd-agency"
MEMORY_FILE = "memory.json"


@dataclass
class MemoryEntry:
    """A single memory entry."""

    key: str
    value: str
    category: str  # terminology, voice, pattern, decision
    source_agent: str = ""
    timestamp: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = time.time()


@dataclass
class ProjectMemory:
    """Project-scoped memory store backed by a JSON file.

    When ``chromadb`` and ``sentence-transformers`` are installed, a
    :class:`~runtime.vector_memory.VectorMemory` is used alongside the
    JSON file to provide semantic search.  The JSON file remains the
    canonical store; vectors are an acceleration layer.
    """

    entries: dict[str, MemoryEntry] = field(default_factory=dict)
    project_dir: Path = field(default_factory=lambda: Path("."))
    _vector: Any = field(default=None, repr=False)

    @property
    def memory_path(self) -> Path:
        return self.project_dir / MEMORY_DIR / MEMORY_FILE

    @property
    def vector(self) -> Any:
        """Lazy-initialize VectorMemory. Returns ``None`` if deps missing."""
        if self._vector is None:
            try:
                from runtime.vector_memory import VectorMemory

                self._vector = VectorMemory(self.project_dir)
            except Exception:
                # chromadb or sentence-transformers not installed
                self._vector = False  # sentinel: tried and failed
        return self._vector if self._vector is not False else None

    @classmethod
    def load(cls, project_dir: Path | None = None) -> ProjectMemory:
        """Load memory from the project directory."""
        project_dir = project_dir or Path(".")
        memory = cls(project_dir=project_dir)
        if memory.memory_path.exists():
            data = json.loads(memory.memory_path.read_text(encoding="utf-8"))
            for key, entry_data in data.get("entries", {}).items():
                memory.entries[key] = MemoryEntry(**entry_data)
            # Auto-migrate JSON entries into vector store if it's empty
            if memory.entries and memory.vector is not None:
                if memory.vector.count() == 0:
                    try:
                        from runtime.vector_memory import migrate_json_to_vectors

                        migrate_json_to_vectors(project_dir)
                    except Exception:
                        pass
        return memory

    def save(self) -> None:
        """Persist memory to disk."""
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": "1.0",
            "entries": {k: asdict(v) for k, v in self.entries.items()},
        }
        self.memory_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def remember(
        self,
        key: str,
        value: str,
        category: str = "decision",
        source_agent: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a memory entry in JSON and (if available) the vector store."""
        self.entries[key] = MemoryEntry(
            key=key,
            value=value,
            category=category,
            source_agent=source_agent,
            metadata=metadata or {},
        )
        self.save()

        if self.vector is not None:
            try:
                self.vector.remember(
                    key=key,
                    value=value,
                    category=category,
                    source_agent=source_agent,
                    metadata=metadata,
                )
            except Exception:
                pass  # Vector store should never break core memory

    def recall(self, key: str) -> MemoryEntry | None:
        """Retrieve a specific memory by key."""
        return self.entries.get(key)

    def recall_by_category(self, category: str) -> list[MemoryEntry]:
        """Get all memories in a category."""
        return [e for e in self.entries.values() if e.category == category]

    def search(self, query: str) -> list[MemoryEntry]:
        """Search memories — semantic when available, substring fallback.

        Uses semantic search if the vector store is available and returns
        results. Always falls back to substring matching when semantic
        search is empty or unavailable (e.g. model not downloaded).
        """
        if self.vector is not None:
            try:
                results = self.vector.semantic_search(query)
                if results:
                    return results
            except Exception:
                pass
        # Fallback: substring matching
        query_lower = query.lower()
        return [
            e for e in self.entries.values()
            if query_lower in e.key.lower() or query_lower in e.value.lower()
        ]

    def forget(self, key: str) -> bool:
        """Remove a memory entry from JSON and vector store."""
        if key in self.entries:
            del self.entries[key]
            self.save()
            if self.vector is not None:
                try:
                    self.vector.forget(key)
                except Exception:
                    pass
            return True
        return False

    def clear(self) -> int:
        """Clear all memory. Returns count of entries removed."""
        count = len(self.entries)
        self.entries.clear()
        self.save()
        return count

    def get_context_for_agent(
        self, agent_name: str = "", query: str = ""
    ) -> str:
        """Build a context string from memory for use in agent prompts.

        When *query* is supplied and a vector store is available, returns
        semantically relevant entries instead of dumping all categories.
        """
        # Semantic path — when we have both a query and vector store
        if query and self.vector is not None:
            try:
                return self.vector.get_context_for_agent(
                    agent_name=agent_name, query=query
                )
            except Exception:
                pass  # Fall through to category-based path

        # Category-based path (original behaviour / fallback)
        if not self.entries:
            return ""

        parts = ["## Project Memory\n"]

        # Terminology decisions
        terms = self.recall_by_category("terminology")
        if terms:
            parts.append("### Terminology Decisions")
            for t in terms:
                parts.append(f"- **{t.key}**: {t.value}")

        # Voice decisions
        voice = self.recall_by_category("voice")
        if voice:
            parts.append("\n### Voice & Tone Decisions")
            for v in voice:
                parts.append(f"- {v.key}: {v.value}")

        # Patterns
        patterns = self.recall_by_category("pattern")
        if patterns:
            parts.append("\n### Content Patterns")
            for p in patterns:
                parts.append(f"- {p.key}: {p.value}")

        # General decisions
        decisions = self.recall_by_category("decision")
        if decisions:
            parts.append("\n### Past Decisions")
            for d in decisions:
                parts.append(f"- {d.key}: {d.value}")

        return "\n".join(parts)

    def to_dict(self) -> dict:
        """Export memory as a dictionary."""
        return {
            "project": str(self.project_dir),
            "entry_count": len(self.entries),
            "categories": list(set(e.category for e in self.entries.values())),
            "entries": {k: asdict(v) for k, v in self.entries.items()},
        }

    def __len__(self) -> int:
        return len(self.entries)

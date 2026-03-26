"""Memory hierarchy — unified session > project > workspace resolution.

Provides a single interface that merges context from three memory tiers:
1. **Session** — ephemeral, current interaction context
2. **Project** — per-project decisions, patterns, terminology (existing ProjectMemory)
3. **Workspace** — cross-project learnings shared via ~/.cd-agency/workspace/

The hierarchy is purely additive — ``ProjectMemory`` is used via composition
and its API is unchanged. ``MemoryHierarchy`` adds workspace and session
layers on top.
"""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from runtime.memory import MemoryEntry, ProjectMemory
from runtime.session_memory import SessionMemory
from runtime.workspace_memory import WorkspaceMemory

# Categories that auto-sync to workspace when visibility="workspace"
_AUTO_SYNC_CATEGORIES = {"brand_dna", "terminology", "voice"}


class MemoryHierarchy:
    """Unified memory interface spanning session, project, and workspace tiers."""

    def __init__(
        self,
        project_dir: Path | str | None = None,
        session_id: str | None = None,
        workspace_id: str = "default",
    ) -> None:
        self.project_dir = Path(project_dir) if project_dir else Path(".")
        self.session = SessionMemory(project_dir=self.project_dir, session_id=session_id)
        self.project = ProjectMemory.load(project_dir=self.project_dir)
        self.workspace = WorkspaceMemory.load(workspace_id=workspace_id)

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def remember(
        self,
        key: str,
        value: str,
        category: str = "decision",
        source_agent: str = "",
        visibility: str = "project",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store memory with visibility control.

        Args:
            visibility: ``"session"`` — session context only (ephemeral).
                ``"project"`` — project-scoped (default, existing behaviour).
                ``"workspace"`` — project + workspace (cross-project sharing).
        """
        meta = dict(metadata or {})
        meta["visibility"] = visibility

        if visibility == "session":
            # Session-only: just track as a recent key + topic
            self.session.update_context(
                memory_keys=[key],
                topics=[f"{category}:{key}"],
            )
            return

        # Always store in project memory
        self.project.remember(
            key=key,
            value=value,
            category=category,
            source_agent=source_agent,
            metadata=meta,
        )

        # Track in session
        self.session.update_context(memory_keys=[key])

        if visibility == "workspace":
            ws_meta = dict(meta)
            ws_meta["source_project"] = str(self.project_dir.resolve())
            self.workspace.remember(
                key=key,
                value=value,
                category=category,
                source_agent=source_agent,
                metadata=ws_meta,
            )

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def recall(self, key: str) -> MemoryEntry | None:
        """Recall by key — project takes precedence over workspace."""
        entry = self.project.recall(key)
        if entry:
            self.session.update_context(memory_keys=[key])
            return entry
        return self.workspace.recall(key)

    def recall_by_category(self, category: str) -> list[MemoryEntry]:
        """Recall by category — merge project + workspace, project wins on conflicts."""
        project_entries = self.project.recall_by_category(category)
        project_keys = {e.key for e in project_entries}

        workspace_entries = [
            e for e in self.workspace.recall_by_category(category)
            if e.key not in project_keys
        ]

        return project_entries + workspace_entries

    def search(self, query: str, n_results: int = 5) -> list[MemoryEntry]:
        """Search across all tiers — project results first."""
        project_results = self.project.search(query)
        project_keys = {e.key for e in project_results}

        remaining = n_results - len(project_results)
        workspace_results = []
        if remaining > 0:
            workspace_results = [
                e for e in self.workspace.search(query, n_results=remaining)
                if e.key not in project_keys
            ]

        return (project_results + workspace_results)[:n_results]

    def forget(self, key: str) -> bool:
        """Forget from project and workspace."""
        p = self.project.forget(key)
        w = self.workspace.forget(key)
        return p or w

    # ------------------------------------------------------------------
    # Context for agents
    # ------------------------------------------------------------------

    def get_context_for_agent(self, agent_name: str = "", query: str = "") -> str:
        """Merge context: session > project > workspace (session takes priority).

        Project context uses the existing ``ProjectMemory.get_context_for_agent``
        method. Workspace entries that duplicate project entries are excluded.
        """
        parts: list[str] = []

        # Session context
        session_ctx = self.session.get_active_context()
        if session_ctx:
            parts.append(session_ctx)

        # Project context (unchanged behaviour)
        project_ctx = self.project.get_context_for_agent(agent_name, query)
        if project_ctx:
            parts.append(project_ctx)

        # Workspace context (supplement, not duplicate)
        workspace_ctx = self._format_workspace_context(query, agent_name)
        if workspace_ctx:
            parts.append(workspace_ctx)

        # Track session
        self.session.update_context(agent_name=agent_name)

        return "\n\n---\n\n".join(filter(None, parts))

    def _format_workspace_context(self, query: str, agent_name: str = "") -> str:
        """Format workspace entries, excluding those overridden by project."""
        project_keys = set(self.project.entries.keys())

        if query:
            entries = self.workspace.search(query, n_results=5)
        else:
            entries = list(self.workspace.entries.values())[:10]

        filtered = [e for e in entries if e.key not in project_keys]
        if not filtered:
            return ""

        parts = ["## Workspace Memory (Shared)\n"]
        for entry in filtered[:5]:
            label = entry.category.title() if entry.category else "General"
            source = entry.metadata.get("source_project", "")
            source_note = f" [from {Path(source).name}]" if source else ""
            parts.append(f"- **[{label}] {entry.key}**: {entry.value}{source_note}")

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Promotion / sync
    # ------------------------------------------------------------------

    def promote_to_workspace(self, key: str) -> bool:
        """Promote a project memory entry to workspace level."""
        entry = self.project.recall(key)
        if not entry:
            return False

        meta = dict(entry.metadata)
        meta["source_project"] = str(self.project_dir.resolve())
        meta["promoted_at"] = time.time()

        self.workspace.remember(
            key=entry.key,
            value=entry.value,
            category=entry.category,
            source_agent=entry.source_agent,
            metadata=meta,
        )
        return True

    def sync_to_workspace(self) -> int:
        """Sync all workspace-visible project entries to workspace. Returns count synced."""
        count = 0
        for key, entry in self.project.entries.items():
            visibility = entry.metadata.get("visibility", "project")
            if visibility == "workspace" or entry.category in _AUTO_SYNC_CATEGORIES:
                meta = dict(entry.metadata)
                meta["source_project"] = str(self.project_dir.resolve())
                self.workspace.remember(
                    key=key,
                    value=entry.value,
                    category=entry.category,
                    source_agent=entry.source_agent,
                    metadata=meta,
                )
                count += 1
        return count

    # ------------------------------------------------------------------
    # Pruning
    # ------------------------------------------------------------------

    def prune(self, max_age_days: int = 90, dry_run: bool = False) -> dict[str, int]:
        """Prune old entries from project and workspace memory.

        Returns counts of entries that would be / were removed.
        """
        cutoff = time.time() - (max_age_days * 24 * 3600)
        result = {"project": 0, "workspace": 0, "sessions": 0}

        # Project
        stale_project = [
            k for k, e in self.project.entries.items()
            if e.timestamp and e.timestamp < cutoff
        ]
        result["project"] = len(stale_project)
        if not dry_run:
            for k in stale_project:
                self.project.forget(k)

        # Workspace
        stale_workspace = [
            k for k, e in self.workspace.entries.items()
            if e.timestamp and e.timestamp < cutoff
        ]
        result["workspace"] = len(stale_workspace)
        if not dry_run:
            for k in stale_workspace:
                self.workspace.forget(k)

        # Sessions
        if not dry_run:
            result["sessions"] = SessionMemory.cleanup_old_sessions(
                max_age_days=min(max_age_days, 30)
            )

        return result

    # ------------------------------------------------------------------
    # Export / import
    # ------------------------------------------------------------------

    def export_all(self) -> dict[str, Any]:
        """Export all memory tiers as a dictionary."""
        return {
            "session": asdict(self.session.context),
            "project": self.project.to_dict(),
            "workspace": {
                "workspace_id": self.workspace.workspace_id,
                "entry_count": len(self.workspace),
                "entries": {k: asdict(v) for k, v in self.workspace.entries.items()},
            },
        }

    def import_memory(
        self,
        data: dict[str, Any],
        target: str = "project",
        dedup: bool = True,
    ) -> int:
        """Import entries from a dictionary. Returns count imported."""
        entries = data.get("entries", {})
        count = 0

        for key, entry_data in entries.items():
            if dedup:
                existing = self.project.recall(key) if target == "project" else self.workspace.recall(key)
                if existing:
                    # Keep newer entry
                    if entry_data.get("timestamp", 0) <= existing.timestamp:
                        continue

            if target == "workspace":
                self.workspace.remember(
                    key=entry_data.get("key", key),
                    value=entry_data.get("value", ""),
                    category=entry_data.get("category", "decision"),
                    source_agent=entry_data.get("source_agent", ""),
                    metadata=entry_data.get("metadata", {}),
                )
            else:
                self.project.remember(
                    key=entry_data.get("key", key),
                    value=entry_data.get("value", ""),
                    category=entry_data.get("category", "decision"),
                    source_agent=entry_data.get("source_agent", ""),
                    metadata=entry_data.get("metadata", {}),
                )
            count += 1

        return count

    def __len__(self) -> int:
        return len(self.project) + len(self.workspace)

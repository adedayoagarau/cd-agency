"""Evaluation history — tracks quality scores across agent runs.

Stores the last 1000 evaluation entries in a JSON file for trend analysis.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


_HISTORY_DIR = ".cd-agency"
_HISTORY_FILE = "evaluation_history.json"
_MAX_ENTRIES = 1000


class EvaluationHistory:
    """Append-only evaluation log with trend retrieval."""

    def __init__(self, project_dir: Path | None = None) -> None:
        self.project_dir = project_dir or Path(".")
        self._history: list[dict[str, Any]] | None = None

    @property
    def storage_path(self) -> Path:
        return self.project_dir / _HISTORY_DIR / _HISTORY_FILE

    @property
    def history(self) -> list[dict[str, Any]]:
        if self._history is None:
            self._history = self._load()
        return self._history

    def _load(self) -> list[dict[str, Any]]:
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def _save(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        # Keep only the last _MAX_ENTRIES
        trimmed = self.history[-_MAX_ENTRIES:]
        self.storage_path.write_text(
            json.dumps(trimmed, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def record(
        self,
        agent_slug: str,
        scores: dict[str, Any],
        composite_score: float,
        passed: bool,
        iteration_count: int = 1,
    ) -> None:
        """Record an evaluation result."""
        entry: dict[str, Any] = {
            "timestamp": time.time(),
            "agent_slug": agent_slug,
            "scores": scores,
            "composite_score": round(composite_score, 2),
            "passed": passed,
            "iteration_count": iteration_count,
        }
        self.history.append(entry)
        self._save()

    def get_trends(
        self, agent_slug: str, metric: str, days: int = 30
    ) -> list[float]:
        """Return recent metric values for an agent."""
        cutoff = time.time() - (days * 24 * 3600)
        return [
            entry["scores"].get(metric, 0)
            for entry in self.history
            if entry.get("agent_slug") == agent_slug
            and entry.get("timestamp", 0) > cutoff
        ]

    def get_pass_rate(self, agent_slug: str, days: int = 30) -> float:
        """Return the pass rate (0.0–1.0) for an agent over the given period."""
        cutoff = time.time() - (days * 24 * 3600)
        entries = [
            e for e in self.history
            if e.get("agent_slug") == agent_slug
            and e.get("timestamp", 0) > cutoff
        ]
        if not entries:
            return 0.0
        passed = sum(1 for e in entries if e.get("passed"))
        return passed / len(entries)

    def count(self) -> int:
        return len(self.history)

    def clear(self) -> int:
        """Clear all history. Returns count removed."""
        n = len(self.history)
        self._history = []
        self._save()
        return n

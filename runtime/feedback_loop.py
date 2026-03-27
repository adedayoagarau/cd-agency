"""Feedback-driven learning — captures human edits and learns from corrections.

When a content designer edits an agent's output, the delta is signal.
This module:
- Captures before/after edits
- Extracts recurring correction patterns
- Stores learnings in brand DNA and project memory
- Improves future agent outputs based on feedback history
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher, unified_diff
from pathlib import Path
from typing import Any


_FEEDBACK_DIR = ".cd-agency/feedback"
_EDITS_FILE = "edits.json"
_PATTERNS_FILE = "patterns.json"
_MAX_EDITS = 500
_MAX_PATTERNS = 200
_PATTERN_THRESHOLD = 2  # Minimum occurrences to become a pattern


@dataclass
class ContentEdit:
    """Captures a single human edit to agent output."""

    id: str = ""
    timestamp: float = 0.0
    agent_slug: str = ""
    agent_name: str = ""
    original: str = ""
    edited: str = ""
    similarity: float = 0.0  # 0-1, how similar original and edited are
    edit_type: str = ""  # "minor_tweak", "significant_rewrite", "rejection"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = time.time()
        if self.original and self.edited and not self.similarity:
            self.similarity = SequenceMatcher(
                None, self.original, self.edited
            ).ratio()
        if not self.edit_type and self.similarity:
            if self.similarity > 0.9:
                self.edit_type = "minor_tweak"
            elif self.similarity > 0.5:
                self.edit_type = "significant_rewrite"
            else:
                self.edit_type = "rejection"

    def diff(self) -> str:
        """Generate a unified diff of the edit."""
        original_lines = self.original.splitlines(keepends=True)
        edited_lines = self.edited.splitlines(keepends=True)
        return "".join(
            unified_diff(original_lines, edited_lines, fromfile="original", tofile="edited")
        )


@dataclass
class EditPattern:
    """A recurring correction pattern learned from multiple edits."""

    id: str = ""
    pattern_type: str = ""  # "word_replacement", "tone_shift", "structure_change", "removal", "addition"
    description: str = ""
    original_pattern: str = ""  # What agents tend to write
    corrected_pattern: str = ""  # What humans correct it to
    occurrences: int = 0
    agent_slugs: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1
    first_seen: float = 0.0
    last_seen: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        now = time.time()
        if not self.first_seen:
            self.first_seen = now
        if not self.last_seen:
            self.last_seen = now

    def build_instruction(self) -> str:
        """Convert pattern to an instruction for agent prompts."""
        if self.original_pattern and self.corrected_pattern:
            return (
                f"Based on past feedback ({self.occurrences}x): "
                f"Use \"{self.corrected_pattern}\" instead of \"{self.original_pattern}\". "
                f"({self.description})"
            )
        return f"Based on past feedback: {self.description}"


class FeedbackStore:
    """Persists content edits and learned patterns."""

    def __init__(self, project_dir: Path | str | None = None) -> None:
        self.project_dir = Path(project_dir) if project_dir else Path(".")
        self._edits: list[ContentEdit] | None = None
        self._patterns: list[EditPattern] | None = None

    @property
    def edits_path(self) -> Path:
        return self.project_dir / _FEEDBACK_DIR / _EDITS_FILE

    @property
    def patterns_path(self) -> Path:
        return self.project_dir / _FEEDBACK_DIR / _PATTERNS_FILE

    @property
    def edits(self) -> list[ContentEdit]:
        if self._edits is None:
            self._edits = self._load_edits()
        return self._edits

    @property
    def patterns(self) -> list[EditPattern]:
        if self._patterns is None:
            self._patterns = self._load_patterns()
        return self._patterns

    # ------------------------------------------------------------------
    # Load / save
    # ------------------------------------------------------------------

    def _load_edits(self) -> list[ContentEdit]:
        if self.edits_path.exists():
            try:
                data = json.loads(self.edits_path.read_text(encoding="utf-8"))
                return [ContentEdit(**e) for e in data] if isinstance(data, list) else []
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        return []

    def _load_patterns(self) -> list[EditPattern]:
        if self.patterns_path.exists():
            try:
                data = json.loads(self.patterns_path.read_text(encoding="utf-8"))
                return [EditPattern(**p) for p in data] if isinstance(data, list) else []
            except (json.JSONDecodeError, TypeError, OSError):
                pass
        return []

    def _save_edits(self) -> None:
        self.edits_path.parent.mkdir(parents=True, exist_ok=True)
        trimmed = self.edits[-_MAX_EDITS:]
        self.edits_path.write_text(
            json.dumps([asdict(e) for e in trimmed], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _save_patterns(self) -> None:
        self.patterns_path.parent.mkdir(parents=True, exist_ok=True)
        trimmed = sorted(self.patterns, key=lambda p: p.occurrences, reverse=True)[:_MAX_PATTERNS]
        self.patterns_path.write_text(
            json.dumps([asdict(p) for p in trimmed], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Record edits
    # ------------------------------------------------------------------

    def record_edit(
        self,
        agent_slug: str,
        original: str,
        edited: str,
        agent_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ContentEdit:
        """Record a human edit to agent output."""
        if original == edited:
            # No change — don't record
            edit = ContentEdit(
                agent_slug=agent_slug,
                agent_name=agent_name,
                original=original,
                edited=edited,
                similarity=1.0,
                edit_type="no_change",
            )
            return edit

        edit = ContentEdit(
            agent_slug=agent_slug,
            agent_name=agent_name,
            original=original,
            edited=edited,
            metadata=metadata or {},
        )
        self.edits.append(edit)
        self._save_edits()

        # Try to detect patterns
        self._detect_patterns(edit)

        return edit

    # ------------------------------------------------------------------
    # Pattern detection
    # ------------------------------------------------------------------

    def _detect_patterns(self, edit: ContentEdit) -> None:
        """Detect word replacement patterns from the edit."""
        original_words = set(edit.original.lower().split())
        edited_words = set(edit.edited.lower().split())

        # Words removed
        removed = original_words - edited_words
        # Words added
        added = edited_words - original_words

        # Simple word replacement detection
        if len(removed) <= 3 and len(added) <= 3 and removed and added:
            for old_word in removed:
                for new_word in added:
                    self._record_replacement(
                        old_word, new_word, edit.agent_slug, "word_replacement"
                    )

    def _record_replacement(
        self, original: str, replacement: str, agent_slug: str, pattern_type: str
    ) -> None:
        """Record or update a replacement pattern."""
        # Check if pattern already exists
        for pattern in self.patterns:
            if (
                pattern.original_pattern.lower() == original.lower()
                and pattern.corrected_pattern.lower() == replacement.lower()
            ):
                pattern.occurrences += 1
                pattern.last_seen = time.time()
                if agent_slug not in pattern.agent_slugs:
                    pattern.agent_slugs.append(agent_slug)
                pattern.confidence = min(1.0, pattern.occurrences / 10)
                self._save_patterns()
                return

        # Create new pattern
        pattern = EditPattern(
            pattern_type=pattern_type,
            description=f"Replace '{original}' with '{replacement}'",
            original_pattern=original,
            corrected_pattern=replacement,
            occurrences=1,
            agent_slugs=[agent_slug],
            confidence=0.1,
        )
        self.patterns.append(pattern)
        self._save_patterns()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_patterns_for_agent(self, agent_slug: str) -> list[EditPattern]:
        """Get patterns relevant to a specific agent."""
        return [
            p for p in self.patterns
            if agent_slug in p.agent_slugs or not p.agent_slugs
        ]

    def get_high_confidence_patterns(self, min_confidence: float = 0.3) -> list[EditPattern]:
        """Get patterns above a confidence threshold."""
        return [p for p in self.patterns if p.confidence >= min_confidence]

    def get_frequent_patterns(self, min_occurrences: int = _PATTERN_THRESHOLD) -> list[EditPattern]:
        """Get patterns that have occurred at least N times."""
        return [p for p in self.patterns if p.occurrences >= min_occurrences]

    def build_feedback_context(self, agent_slug: str) -> str:
        """Build a context block from learned patterns for injection into agent prompts."""
        patterns = self.get_patterns_for_agent(agent_slug)
        # Only use patterns with enough occurrences
        relevant = [p for p in patterns if p.occurrences >= _PATTERN_THRESHOLD]

        if not relevant:
            return ""

        parts = ["## Learned Feedback Patterns\n"]
        parts.append("Based on past human corrections, follow these guidelines:\n")

        for p in sorted(relevant, key=lambda x: x.occurrences, reverse=True)[:10]:
            parts.append(f"- {p.build_instruction()}")

        return "\n".join(parts)

    def get_agent_edit_stats(self, agent_slug: str) -> dict[str, Any]:
        """Get editing statistics for an agent."""
        agent_edits = [e for e in self.edits if e.agent_slug == agent_slug]
        if not agent_edits:
            return {
                "total_edits": 0,
                "avg_similarity": 0.0,
                "minor_tweaks": 0,
                "significant_rewrites": 0,
                "rejections": 0,
            }

        return {
            "total_edits": len(agent_edits),
            "avg_similarity": sum(e.similarity for e in agent_edits) / len(agent_edits),
            "minor_tweaks": sum(1 for e in agent_edits if e.edit_type == "minor_tweak"),
            "significant_rewrites": sum(1 for e in agent_edits if e.edit_type == "significant_rewrite"),
            "rejections": sum(1 for e in agent_edits if e.edit_type == "rejection"),
        }

    def sync_to_memory(self, memory: Any) -> int:
        """Sync high-confidence patterns to project memory."""
        synced = 0
        for pattern in self.get_high_confidence_patterns(min_confidence=0.5):
            try:
                memory.remember(
                    key=f"feedback:{pattern.id}",
                    value=pattern.build_instruction(),
                    category="feedback",
                    source_agent="feedback_loop",
                )
                synced += 1
            except Exception:
                pass
        return synced

    def edit_count(self) -> int:
        return len(self.edits)

    def pattern_count(self) -> int:
        return len(self.patterns)

    def clear_edits(self) -> int:
        n = len(self.edits)
        self._edits = []
        self._save_edits()
        return n

    def clear_patterns(self) -> int:
        n = len(self.patterns)
        self._patterns = []
        self._save_patterns()
        return n

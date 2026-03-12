"""Content versioning — tracks before/after for every agent run.

Stores a history of content transformations so users can compare,
review, and roll back agent outputs. Backed by a local JSON file.
"""

from __future__ import annotations

import json
import time
import hashlib
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


VERSION_DIR = ".cd-agency"
VERSION_FILE = "content_versions.json"
MAX_VERSIONS = 200  # Prevent unbounded growth


@dataclass
class ContentVersion:
    """A single version entry tracking an agent transformation."""

    id: str
    timestamp: float
    agent_name: str
    agent_slug: str
    input_text: str
    output_text: str
    input_fields: dict[str, str] = field(default_factory=dict)
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def input_preview(self) -> str:
        return self.input_text[:80] + ("..." if len(self.input_text) > 80 else "")

    @property
    def output_preview(self) -> str:
        return self.output_text[:80] + ("..." if len(self.output_text) > 80 else "")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ContentHistory:
    """Versioned content history backed by a JSON file."""

    versions: list[ContentVersion] = field(default_factory=list)
    project_dir: Path = field(default_factory=lambda: Path("."))

    @property
    def history_path(self) -> Path:
        return self.project_dir / VERSION_DIR / VERSION_FILE

    @classmethod
    def load(cls, project_dir: Path | None = None) -> ContentHistory:
        """Load version history from disk."""
        project_dir = project_dir or Path(".")
        history = cls(project_dir=project_dir)
        if history.history_path.exists():
            data = json.loads(history.history_path.read_text(encoding="utf-8"))
            for entry in data.get("versions", []):
                history.versions.append(ContentVersion(**entry))
        return history

    def save(self) -> None:
        """Persist version history to disk."""
        self.history_path.parent.mkdir(parents=True, exist_ok=True)
        # Trim to max versions (keep most recent)
        if len(self.versions) > MAX_VERSIONS:
            self.versions = self.versions[-MAX_VERSIONS:]
        data = {
            "version": "1.0",
            "count": len(self.versions),
            "versions": [v.to_dict() for v in self.versions],
        }
        self.history_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def record(
        self,
        agent_name: str,
        agent_slug: str,
        input_text: str,
        output_text: str,
        *,
        input_fields: dict[str, str] | None = None,
        model: str = "",
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        tags: list[str] | None = None,
        notes: str = "",
    ) -> ContentVersion:
        """Record a new content version."""
        ts = time.time()
        # Generate a short ID from timestamp + agent
        raw = f"{ts}-{agent_slug}-{input_text[:50]}"
        version_id = hashlib.sha256(raw.encode()).hexdigest()[:12]

        version = ContentVersion(
            id=version_id,
            timestamp=ts,
            agent_name=agent_name,
            agent_slug=agent_slug,
            input_text=input_text,
            output_text=output_text,
            input_fields=input_fields or {},
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            tags=tags or [],
            notes=notes,
        )
        self.versions.append(version)
        self.save()
        return version

    def get(self, version_id: str) -> ContentVersion | None:
        """Get a specific version by ID."""
        for v in self.versions:
            if v.id == version_id:
                return v
        return None

    def list_recent(self, count: int = 20) -> list[ContentVersion]:
        """Get the most recent versions."""
        return list(reversed(self.versions[-count:]))

    def list_by_agent(self, agent_slug: str) -> list[ContentVersion]:
        """Get all versions produced by a specific agent."""
        return [v for v in self.versions if v.agent_slug == agent_slug]

    def search(self, query: str) -> list[ContentVersion]:
        """Search versions by input/output text."""
        q = query.lower()
        return [
            v for v in self.versions
            if q in v.input_text.lower() or q in v.output_text.lower()
            or q in v.notes.lower()
        ]

    def diff(self, version_id: str) -> dict[str, Any] | None:
        """Get a before/after diff for a version."""
        v = self.get(version_id)
        if not v:
            return None
        return {
            "id": v.id,
            "agent": v.agent_name,
            "timestamp": v.timestamp,
            "before": v.input_text,
            "after": v.output_text,
            "before_len": len(v.input_text),
            "after_len": len(v.output_text),
            "char_delta": len(v.output_text) - len(v.input_text),
        }

    def clear(self) -> int:
        """Clear all version history. Returns count of entries removed."""
        count = len(self.versions)
        self.versions.clear()
        self.save()
        return count

    @property
    def count(self) -> int:
        return len(self.versions)

    def summary(self) -> dict[str, Any]:
        """Summary stats for the version history."""
        if not self.versions:
            return {"count": 0, "agents_used": [], "latest": None}

        agents = list(set(v.agent_slug for v in self.versions))
        latest = self.versions[-1]
        return {
            "count": len(self.versions),
            "agents_used": agents,
            "latest": {
                "id": latest.id,
                "agent": latest.agent_name,
                "timestamp": latest.timestamp,
                "preview": latest.output_preview,
            },
        }

"""Session memory — tracks context within a single CLI session.

Sessions capture what an agent has been working on, which memory keys
were accessed, and active topics. Sessions are persisted to disk so
they can be resumed across CLI invocations.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


_SESSION_DIR = ".cd-agency"
_SESSION_FILE = "session.json"
_WORKSPACE_SESSIONS_DIR = Path.home() / ".cd-agency" / "workspace" / "sessions"
_MAX_TOPICS = 50
_MAX_RECENT_KEYS = 20
_DEFAULT_SESSION_TTL_DAYS = 7


@dataclass
class SessionContext:
    """Tracks the current session state."""

    session_id: str = ""
    project_path: str = ""
    start_time: float = 0.0
    last_activity: float = 0.0
    active_topics: list[str] = field(default_factory=list)
    recent_keys: list[str] = field(default_factory=list)
    agent_interactions: int = 0

    def __post_init__(self) -> None:
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        now = time.time()
        if not self.start_time:
            self.start_time = now
        if not self.last_activity:
            self.last_activity = now


class SessionMemory:
    """Manages session-level context within a project directory.

    Session context is lightweight — it stores topics and accessed keys,
    not full memory entries. Sessions auto-expire after ``max_age_days``.
    """

    def __init__(
        self,
        project_dir: Path | str | None = None,
        session_id: str | None = None,
    ) -> None:
        self.project_dir = Path(project_dir) if project_dir else Path(".")
        self.session_file = self.project_dir / _SESSION_DIR / _SESSION_FILE
        self._context: SessionContext | None = None

        # Try to resume existing session or create new
        if session_id:
            loaded = self._load_session(session_id)
            if loaded:
                self._context = loaded
        if self._context is None:
            self._context = SessionContext(
                session_id=session_id or str(uuid.uuid4()),
                project_path=str(self.project_dir.resolve()),
            )

    @property
    def context(self) -> SessionContext:
        return self._context  # type: ignore[return-value]

    @property
    def session_id(self) -> str:
        return self.context.session_id

    def update_context(
        self,
        agent_name: str = "",
        memory_keys: list[str] | None = None,
        topics: list[str] | None = None,
    ) -> None:
        """Update session context after an agent interaction."""
        self.context.last_activity = time.time()
        self.context.agent_interactions += 1

        if memory_keys:
            for key in memory_keys:
                if key not in self.context.recent_keys:
                    self.context.recent_keys.append(key)
            self.context.recent_keys = self.context.recent_keys[-_MAX_RECENT_KEYS:]

        if topics:
            for topic in topics:
                if topic not in self.context.active_topics:
                    self.context.active_topics.append(topic)
            self.context.active_topics = self.context.active_topics[-_MAX_TOPICS:]

        if agent_name and agent_name not in self.context.active_topics:
            self.context.active_topics.append(f"agent:{agent_name}")
            self.context.active_topics = self.context.active_topics[-_MAX_TOPICS:]

        self.save_session()

    def get_active_context(self) -> str:
        """Build a context string from current session state."""
        if not self.context.active_topics and not self.context.recent_keys:
            return ""

        parts = ["## Session Context\n"]

        if self.context.active_topics:
            agent_topics = [t for t in self.context.active_topics if t.startswith("agent:")]
            other_topics = [t for t in self.context.active_topics if not t.startswith("agent:")]

            if agent_topics:
                agents = [t.split(":", 1)[1] for t in agent_topics[-5:]]
                parts.append(f"Recent agents: {', '.join(agents)}")

            if other_topics:
                parts.append(f"Active topics: {', '.join(other_topics[-10:])}")

        if self.context.recent_keys:
            parts.append(f"Recently accessed memory: {', '.join(self.context.recent_keys[-5:])}")

        parts.append(f"Session interactions: {self.context.agent_interactions}")

        return "\n".join(parts)

    def save_session(self) -> None:
        """Persist session to project directory and workspace sessions."""
        self.session_file.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self.context)
        self.session_file.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # Also save to workspace sessions for cross-session listing
        try:
            _WORKSPACE_SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
            ws_file = _WORKSPACE_SESSIONS_DIR / f"{self.context.session_id}.json"
            ws_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass  # Workspace session save is best-effort

    def _load_session(self, session_id: str) -> SessionContext | None:
        """Try to load a specific session from the project directory."""
        if self.session_file.exists():
            try:
                data = json.loads(self.session_file.read_text(encoding="utf-8"))
                if data.get("session_id") == session_id:
                    return SessionContext(**data)
            except (json.JSONDecodeError, TypeError):
                pass

        return None

    @staticmethod
    def load_current(project_dir: Path | str | None = None) -> SessionMemory:
        """Load the most recent session for a project, or create new."""
        project_dir = Path(project_dir) if project_dir else Path(".")
        session_file = project_dir / _SESSION_DIR / _SESSION_FILE

        if session_file.exists():
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
                session_id = data.get("session_id", "")
                if session_id:
                    return SessionMemory(project_dir=project_dir, session_id=session_id)
            except (json.JSONDecodeError, TypeError):
                pass

        return SessionMemory(project_dir=project_dir)

    @staticmethod
    def list_sessions(max_count: int = 20) -> list[dict[str, Any]]:
        """List recent sessions from workspace."""
        sessions: list[dict[str, Any]] = []

        if not _WORKSPACE_SESSIONS_DIR.exists():
            return sessions

        for f in sorted(
            _WORKSPACE_SESSIONS_DIR.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:max_count]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                sessions.append({
                    "session_id": data.get("session_id", f.stem),
                    "project_path": data.get("project_path", ""),
                    "start_time": data.get("start_time", 0),
                    "last_activity": data.get("last_activity", 0),
                    "interactions": data.get("agent_interactions", 0),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return sessions

    @staticmethod
    def cleanup_old_sessions(max_age_days: int = _DEFAULT_SESSION_TTL_DAYS) -> int:
        """Remove expired sessions from workspace. Returns count removed."""
        if not _WORKSPACE_SESSIONS_DIR.exists():
            return 0

        cutoff = time.time() - (max_age_days * 24 * 3600)
        removed = 0

        for f in _WORKSPACE_SESSIONS_DIR.glob("*.json"):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                last = data.get("last_activity", 0)
                if last and last < cutoff:
                    f.unlink()
                    removed += 1
            except (json.JSONDecodeError, OSError):
                # Corrupted — remove
                try:
                    f.unlink()
                    removed += 1
                except OSError:
                    pass

        return removed

"""Tests for SessionMemory."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from runtime.session_memory import SessionMemory, SessionContext, _WORKSPACE_SESSIONS_DIR


class TestSessionContext:
    def test_default_values(self):
        ctx = SessionContext()
        assert ctx.session_id != ""
        assert ctx.start_time > 0
        assert ctx.last_activity > 0
        assert ctx.agent_interactions == 0

    def test_explicit_id(self):
        ctx = SessionContext(session_id="test-123")
        assert ctx.session_id == "test-123"


class TestSessionMemory:
    def test_create_new_session(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        assert sm.session_id != ""
        assert sm.context.agent_interactions == 0

    def test_update_context(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        sm.update_context(
            agent_name="Error Message Architect",
            memory_keys=["error-tone", "validation-rules"],
            topics=["error messages", "form validation"],
        )
        assert sm.context.agent_interactions == 1
        assert "error-tone" in sm.context.recent_keys
        assert "validation-rules" in sm.context.recent_keys
        assert "error messages" in sm.context.active_topics
        assert "agent:Error Message Architect" in sm.context.active_topics

    def test_update_context_multiple(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        sm.update_context(agent_name="Agent1")
        sm.update_context(agent_name="Agent2")
        assert sm.context.agent_interactions == 2

    def test_get_active_context_empty(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        assert sm.get_active_context() == ""

    def test_get_active_context_with_data(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        sm.update_context(
            agent_name="Test Agent",
            memory_keys=["key1"],
            topics=["topic1"],
        )
        ctx = sm.get_active_context()
        assert "Session Context" in ctx
        assert "Test Agent" in ctx
        assert "topic1" in ctx

    def test_max_recent_keys(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        keys = [f"key-{i}" for i in range(30)]
        sm.update_context(memory_keys=keys)
        assert len(sm.context.recent_keys) <= 20

    def test_max_topics(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path)
        topics = [f"topic-{i}" for i in range(60)]
        sm.update_context(topics=topics)
        assert len(sm.context.active_topics) <= 50


class TestSessionPersistence:
    def test_save_and_load(self, tmp_path):
        sm1 = SessionMemory(project_dir=tmp_path, session_id="test-persist")
        sm1.update_context(agent_name="Agent1", topics=["testing"])
        sm1.save_session()

        # Load same session
        sm2 = SessionMemory(project_dir=tmp_path, session_id="test-persist")
        assert sm2.context.session_id == "test-persist"
        assert sm2.context.agent_interactions == 1
        assert "testing" in sm2.context.active_topics

    def test_load_current(self, tmp_path):
        sm1 = SessionMemory(project_dir=tmp_path, session_id="current-test")
        sm1.save_session()

        sm2 = SessionMemory.load_current(project_dir=tmp_path)
        assert sm2.context.session_id == "current-test"

    def test_load_current_no_session(self, tmp_path):
        sm = SessionMemory.load_current(project_dir=tmp_path)
        assert sm.session_id != ""  # New session created

    def test_load_nonexistent_session(self, tmp_path):
        sm = SessionMemory(project_dir=tmp_path, session_id="nonexistent")
        # Should create new context with that ID
        assert sm.context.session_id == "nonexistent"
        assert sm.context.agent_interactions == 0


class TestSessionListAndCleanup:
    def test_list_sessions(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        for i in range(3):
            data = {
                "session_id": f"session-{i}",
                "project_path": f"/project/{i}",
                "start_time": time.time(),
                "last_activity": time.time(),
                "agent_interactions": i,
                "active_topics": [],
                "recent_keys": [],
            }
            (sessions_dir / f"session-{i}.json").write_text(
                json.dumps(data), encoding="utf-8"
            )

        with patch("runtime.session_memory._WORKSPACE_SESSIONS_DIR", sessions_dir):
            sessions = SessionMemory.list_sessions()
            assert len(sessions) == 3

    def test_cleanup_old_sessions(self, tmp_path):
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir(parents=True)

        # Create an old session
        old_data = {
            "session_id": "old-session",
            "project_path": "/old",
            "start_time": 1000,
            "last_activity": 1000,  # Very old
            "agent_interactions": 1,
            "active_topics": [],
            "recent_keys": [],
        }
        (sessions_dir / "old-session.json").write_text(
            json.dumps(old_data), encoding="utf-8"
        )

        # Create a recent session
        recent_data = {
            "session_id": "recent-session",
            "project_path": "/recent",
            "start_time": time.time(),
            "last_activity": time.time(),
            "agent_interactions": 1,
            "active_topics": [],
            "recent_keys": [],
        }
        (sessions_dir / "recent-session.json").write_text(
            json.dumps(recent_data), encoding="utf-8"
        )

        with patch("runtime.session_memory._WORKSPACE_SESSIONS_DIR", sessions_dir):
            removed = SessionMemory.cleanup_old_sessions(max_age_days=1)
            assert removed == 1
            assert not (sessions_dir / "old-session.json").exists()
            assert (sessions_dir / "recent-session.json").exists()

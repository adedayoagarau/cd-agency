"""Tests for WebSocket streaming module."""
from __future__ import annotations

import json
import time

import pytest


class TestStreamEvent:
    def test_create_event(self):
        from packages.cloud.streaming.websocket import StreamEvent

        event = StreamEvent(event_type="start", data={"run_id": "r1"})
        assert event.event_type == "start"
        assert event.data["run_id"] == "r1"
        assert event.timestamp > 0

    def test_event_to_json(self):
        from packages.cloud.streaming.websocket import StreamEvent

        event = StreamEvent(
            event_type="token",
            data={"content": "Hello"},
            timestamp=1234567890.0,
        )
        result = json.loads(event.to_json())
        assert result["event_type"] == "token"
        assert result["data"]["content"] == "Hello"
        assert result["timestamp"] == 1234567890.0

    def test_event_types(self):
        from packages.cloud.streaming.websocket import StreamEvent

        for event_type in ["start", "token", "tool_call", "tool_result", "complete", "error"]:
            event = StreamEvent(event_type=event_type, data={})
            assert event.event_type == event_type

    def test_event_default_timestamp(self):
        from packages.cloud.streaming.websocket import StreamEvent

        before = time.time()
        event = StreamEvent(event_type="start", data={})
        after = time.time()
        assert before <= event.timestamp <= after


class TestAgentStreamManager:
    def test_init_empty(self):
        from packages.cloud.streaming.websocket import AgentStreamManager

        mgr = AgentStreamManager()
        assert mgr._connections == {}

    @pytest.mark.asyncio
    async def test_connect_and_disconnect(self):
        from packages.cloud.streaming.websocket import AgentStreamManager

        mgr = AgentStreamManager()
        ws = object()
        await mgr.connect("run1", ws)
        assert "run1" in mgr._connections
        assert ws in mgr._connections["run1"]

        await mgr.disconnect("run1", ws)
        assert "run1" not in mgr._connections

    @pytest.mark.asyncio
    async def test_disconnect_nonexistent(self):
        from packages.cloud.streaming.websocket import AgentStreamManager

        mgr = AgentStreamManager()
        # Should not raise
        await mgr.disconnect("nonexistent", object())

    @pytest.mark.asyncio
    async def test_broadcast(self):
        from packages.cloud.streaming.websocket import AgentStreamManager, StreamEvent

        mgr = AgentStreamManager()
        messages = []

        class FakeWS:
            async def send(self, msg):
                messages.append(msg)

        ws = FakeWS()
        await mgr.connect("run1", ws)

        event = StreamEvent(event_type="token", data={"content": "hi"})
        await mgr.broadcast("run1", event)

        assert len(messages) == 1
        parsed = json.loads(messages[0])
        assert parsed["event_type"] == "token"
        assert parsed["data"]["content"] == "hi"

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple(self):
        from packages.cloud.streaming.websocket import AgentStreamManager, StreamEvent

        mgr = AgentStreamManager()
        messages1 = []
        messages2 = []

        class FakeWS1:
            async def send(self, msg):
                messages1.append(msg)

        class FakeWS2:
            async def send(self, msg):
                messages2.append(msg)

        await mgr.connect("run1", FakeWS1())
        await mgr.connect("run1", FakeWS2())

        event = StreamEvent(event_type="complete", data={"output": "done"})
        await mgr.broadcast("run1", event)

        assert len(messages1) == 1
        assert len(messages2) == 1

    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self):
        from packages.cloud.streaming.websocket import AgentStreamManager, StreamEvent

        mgr = AgentStreamManager()

        class DeadWS:
            async def send(self, msg):
                raise ConnectionError("disconnected")

        ws = DeadWS()
        await mgr.connect("run1", ws)

        event = StreamEvent(event_type="token", data={})
        await mgr.broadcast("run1", event)

        # Dead connection should be removed
        assert ws not in mgr._connections.get("run1", [])

    @pytest.mark.asyncio
    async def test_broadcast_to_empty_run(self):
        from packages.cloud.streaming.websocket import AgentStreamManager, StreamEvent

        mgr = AgentStreamManager()
        event = StreamEvent(event_type="token", data={})
        # Should not raise
        await mgr.broadcast("nonexistent", event)

"""WebSocket streaming for real-time agent output delivery."""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, Generator


@dataclass
class StreamEvent:
    """A single event emitted during an agent run stream.

    Event types: ``start``, ``token``, ``tool_call``, ``tool_result``,
    ``complete``, ``error``.
    """

    event_type: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> str:
        """Serialise the event to a JSON string suitable for WebSocket transmission."""
        return json.dumps(
            {
                "event_type": self.event_type,
                "data": self.data,
                "timestamp": self.timestamp,
            }
        )


class AgentStreamManager:
    """Manages WebSocket connections and broadcasts ``StreamEvent`` objects.

    Each *run_id* can have multiple connected WebSocket clients.  Events are
    broadcast to all of them.
    """

    def __init__(self) -> None:
        self._connections: dict[str, list[Any]] = {}

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    async def connect(self, run_id: str, websocket: Any) -> None:
        """Register *websocket* to receive events for *run_id*."""
        if run_id not in self._connections:
            self._connections[run_id] = []
        self._connections[run_id].append(websocket)

    async def disconnect(self, run_id: str, websocket: Any) -> None:
        """Remove *websocket* from *run_id* listeners."""
        conns = self._connections.get(run_id)
        if conns is None:
            return
        try:
            conns.remove(websocket)
        except ValueError:
            pass
        if not conns:
            del self._connections[run_id]

    # ------------------------------------------------------------------
    # Broadcasting
    # ------------------------------------------------------------------

    async def broadcast(self, run_id: str, event: StreamEvent) -> None:
        """Send *event* to every WebSocket listening on *run_id*."""
        conns = self._connections.get(run_id)
        if not conns:
            return

        message = event.to_json()
        dead: list[Any] = []

        for ws in conns:
            try:
                await ws.send(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)

        # Clean up broken connections.
        for ws in dead:
            try:
                conns.remove(ws)
            except ValueError:
                pass

    # ------------------------------------------------------------------
    # Agent run streaming
    # ------------------------------------------------------------------

    async def stream_agent_run(
        self,
        run_id: str,
        agent_slug: str,
        input_text: str,
        org_id: str,
        project_id: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Execute an agent run and yield ``StreamEvent`` objects.

        This is an async generator so callers can iterate over the events
        while they are simultaneously broadcast to connected WebSocket clients.

        Event flow:
        1. ``start`` – run begins
        2. ``token`` – streamed tokens (zero or more)
        3. ``tool_call`` / ``tool_result`` – tool interactions (zero or more)
        4. ``complete`` or ``error`` – run finishes
        """
        # --- start ---
        start_event = StreamEvent(
            event_type="start",
            data={
                "run_id": run_id,
                "agent_slug": agent_slug,
                "org_id": org_id,
                "project_id": project_id,
            },
        )
        await self.broadcast(run_id, start_event)
        yield start_event

        try:
            # Import the agent runner from the core runtime.
            from runtime.runner import run_agent  # type: ignore[import-untyped]

            # The runner is expected to yield dicts with "type" and "content"
            # keys (e.g. {"type": "token", "content": "Hello"}).  We wrap
            # each chunk in a StreamEvent.
            result_chunks: list[str] = []

            for chunk in run_agent(agent_slug, input_text):  # type: ignore[attr-defined]
                chunk_type: str = chunk.get("type", "token") if isinstance(chunk, dict) else "token"
                chunk_data: dict[str, Any]

                if isinstance(chunk, dict):
                    chunk_data = chunk
                else:
                    chunk_data = {"content": str(chunk)}

                if chunk_type == "token":
                    result_chunks.append(chunk_data.get("content", ""))

                event = StreamEvent(event_type=chunk_type, data=chunk_data)
                await self.broadcast(run_id, event)
                yield event

            # --- complete ---
            complete_event = StreamEvent(
                event_type="complete",
                data={
                    "run_id": run_id,
                    "output": "".join(result_chunks),
                },
            )
            await self.broadcast(run_id, complete_event)
            yield complete_event

        except Exception as exc:  # noqa: BLE001
            error_event = StreamEvent(
                event_type="error",
                data={
                    "run_id": run_id,
                    "error": str(exc),
                },
            )
            await self.broadcast(run_id, error_event)
            yield error_event

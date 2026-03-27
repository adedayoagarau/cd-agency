"""WebSocket endpoint for streaming agent run output."""
from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

router = APIRouter(prefix="/v2/ws", tags=["websocket"])


# ---------------------------------------------------------------------------
# In-memory run-output channels (swap for Redis pub/sub in production)
# ---------------------------------------------------------------------------

_channels: dict[str, asyncio.Queue[dict[str, Any]]] = {}


def publish_to_run(run_id: str, message: dict[str, Any]) -> None:
    """Publish a message to the channel for a given run_id.

    Called by the agent runner to stream tokens / status updates.
    """
    queue = _channels.get(run_id)
    if queue is not None:
        queue.put_nowait(message)


def _get_or_create_channel(run_id: str) -> asyncio.Queue[dict[str, Any]]:
    if run_id not in _channels:
        _channels[run_id] = asyncio.Queue()
    return _channels[run_id]


def _remove_channel(run_id: str) -> None:
    _channels.pop(run_id, None)


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@router.websocket("/agent-run/{run_id}")
async def stream_agent_run(websocket: WebSocket, run_id: str) -> None:
    """Stream agent run output over a WebSocket connection.

    Protocol
    --------
    1. Client connects to ``/v2/ws/agent-run/{run_id}``.
    2. Server accepts and begins forwarding JSON messages from the run
       channel.  Each message is a JSON object with at least a ``type`` field
       (``"token"``, ``"status"``, ``"error"``, ``"done"``).
    3. When the run finishes, the server sends ``{"type": "done"}`` and closes
       the connection.
    4. The client may send ``{"type": "cancel"}`` to request cancellation.

    Authentication is intentionally lightweight here — the ``run_id`` itself
    acts as a capability token.  Production deployments should add token
    verification during the handshake (via query param or first message).
    """
    await websocket.accept()

    channel = _get_or_create_channel(run_id)

    try:
        while True:
            try:
                # Wait for a message from the run channel, timing out so we
                # can check for client messages periodically.
                message = await asyncio.wait_for(channel.get(), timeout=1.0)
            except asyncio.TimeoutError:
                # No message yet — check if client sent anything (non-blocking).
                try:
                    client_data = await asyncio.wait_for(
                        websocket.receive_text(), timeout=0.01
                    )
                    client_msg = json.loads(client_data)
                    if client_msg.get("type") == "cancel":
                        await websocket.send_json({"type": "cancelled"})
                        break
                except (asyncio.TimeoutError, json.JSONDecodeError):
                    pass
                continue

            await websocket.send_json(message)

            if message.get("type") == "done":
                break

    except WebSocketDisconnect:
        pass
    finally:
        _remove_channel(run_id)

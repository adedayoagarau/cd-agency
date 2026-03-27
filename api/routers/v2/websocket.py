from __future__ import annotations
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter(tags=["websocket-v2"])

@router.websocket("/api/v2/agents/run/stream")
async def stream_agent_run(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        agent_slug = data.get("agent_slug")
        content = data.get("content")
        anthropic_key = data.get("anthropic_key")
        openai_key = data.get("openai_key")

        from runtime.config import Config
        from runtime.runner import AgentRunner
        from api.deps import get_registry

        registry = get_registry()
        config = Config.from_env()
        if anthropic_key:
            config.api_key = anthropic_key
        if openai_key:
            config.openai_api_key = openai_key
        runner = AgentRunner(config)

        agent = registry.get(agent_slug)
        if not agent:
            await websocket.send_json({"type": "error", "message": f"Agent '{agent_slug}' not found"})
            await websocket.close()
            return

        await websocket.send_json({"type": "status", "message": "Starting agent..."})

        # Build input
        user_input = {"content": content}
        required = agent.get_required_inputs()
        if required and len(required) == 1:
            user_input = {required[0].name: content}

        result = runner.run(agent=agent, user_input=user_input)

        await websocket.send_json({
            "type": "output",
            "content": result.content,
        })

        # Extract council result if available
        council_result = None
        if isinstance(result.raw_response, dict):
            council_result = result.raw_response.get("council")

        await websocket.send_json({
            "type": "evaluation",
            "evaluation": result.evaluation,
            "composite_score": result.composite_score,
            "passed": result.passed,
            "iterations": result.iterations,
            "council_result": council_result,
        })

        await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close()
        except Exception:
            pass

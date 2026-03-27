from __future__ import annotations
from typing import Annotated, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from pathlib import Path
import time
import uuid

from api.models_v2 import RunAgentRequest, RunAgentResponse, AgentSummaryV2
from api.deps import get_registry, get_runner_with_user_key
from runtime.runner import AgentRunner

router = APIRouter(prefix="/api/v2/agents", tags=["agents-v2"])


# ── Chat / Batch Models ─────────────────────────────────────────────────────


class ConversationMessageV2(BaseModel):
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class ConversationRequestV2(BaseModel):
    messages: list[ConversationMessageV2] = Field(
        ..., min_length=1, description="Conversation history"
    )
    preset: str | None = Field(None, description="Optional design system preset name")


class ConversationResponseV2(BaseModel):
    content: str
    agent_name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


class BatchItemV2(BaseModel):
    input: dict[str, Any] = Field(..., description="Input fields for one agent run")


class BatchRequestV2(BaseModel):
    items: list[BatchItemV2] = Field(..., min_length=1, max_length=50)
    preset: str | None = Field(None, description="Optional design system preset")


class BatchItemResponseV2(BaseModel):
    content: str
    agent_name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


# ── Existing Routes ──────────────────────────────────────────────────────────


@router.get("")
async def list_agents(registry=Depends(get_registry)):
    """List all agents with their configs."""
    agents = []
    for agent in registry.list_all():
        agents.append({
            "slug": agent.slug,
            "name": agent.name,
            "description": agent.description,
            "model": agent.preferred_model or "claude-sonnet-4-20250514",
            "tools": getattr(agent, 'tools', []) or [],
            "tags": agent.tags or [],
            "evaluation": {},  # Agent definitions don't store eval weights directly
            "threshold": 0.75,
        })
    return {"agents": agents}

@router.get("/{slug}")
async def get_agent(slug: str, registry=Depends(get_registry)):
    """Get a single agent's config."""
    agent = registry.get(slug)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")
    return {
        "slug": agent.slug,
        "name": agent.name,
        "description": agent.description,
        "model": agent.preferred_model or "claude-sonnet-4-20250514",
        "tools": getattr(agent, 'tools', []) or [],
        "tags": agent.tags or [],
        "inputs": [{"name": i.name, "type": i.type, "required": i.required, "description": i.description} for i in agent.inputs],
        "outputs": [{"name": o.name, "type": o.type, "description": o.description} for o in agent.outputs],
        "evaluation": {},
        "threshold": 0.75,
    }

@router.post("/run", response_model=RunAgentResponse)
async def run_agent(request: RunAgentRequest, registry=Depends(get_registry), runner=Depends(get_runner_with_user_key)):
    """Run an agent and return the result."""
    agent = registry.get(request.agent_slug)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_slug}' not found")

    start = time.time()
    run_id = str(uuid.uuid4())

    try:
        # Build user_input dict - the agent expects a dict with input field names
        # Most agents have a primary "content" or "text" input
        user_input = {"content": request.content}
        # Try to match the agent's required inputs
        required = agent.get_required_inputs()
        if required and len(required) == 1:
            user_input = {required[0].name: request.content}

        result = runner.run(
            agent=agent,
            user_input=user_input,
            model=request.model,
        )

        duration_ms = int((time.time() - start) * 1000)

        # Extract council result if available
        council_result = None
        if isinstance(result.raw_response, dict):
            council_result = result.raw_response.get("council")

        return RunAgentResponse(
            run_id=run_id,
            agent=request.agent_slug,
            output=result.content,
            evaluation=result.evaluation,
            composite_score=result.composite_score,
            passed=result.passed,
            iterations=result.iterations,
            council_result=council_result,
            duration_ms=duration_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Chat Endpoint ────────────────────────────────────────────────────────────


@router.post("/{slug}/chat", response_model=ConversationResponseV2)
async def chat_with_agent(
    slug: str,
    body: ConversationRequestV2,
    registry=Depends(get_registry),
    runner: Annotated[AgentRunner, Depends(get_runner_with_user_key)] = None,
) -> ConversationResponseV2:
    """Run a multi-turn conversation with an agent."""
    agent = registry.get(slug)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")

    messages = [{"role": m.role, "content": m.content} for m in body.messages]

    try:
        output = runner.run_conversation(agent, messages)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Conversation failed: {exc}",
        )

    return ConversationResponseV2(
        content=output.content,
        agent_name=output.agent_name,
        model=output.model,
        input_tokens=output.input_tokens,
        output_tokens=output.output_tokens,
        latency_ms=output.latency_ms,
    )


# ── Batch Endpoint ───────────────────────────────────────────────────────────


@router.post("/{slug}/batch", response_model=list[BatchItemResponseV2])
async def batch_run_agent(
    slug: str,
    body: BatchRequestV2,
    registry=Depends(get_registry),
    runner: Annotated[AgentRunner, Depends(get_runner_with_user_key)] = None,
) -> list[BatchItemResponseV2]:
    """Run an agent on multiple inputs sequentially (up to 50 items)."""
    agent = registry.get(slug)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{slug}' not found")

    results = []
    for item in body.items:
        try:
            output = runner.run(agent, item.input)
            results.append(BatchItemResponseV2(
                content=output.content,
                agent_name=output.agent_name,
                model=output.model,
                input_tokens=output.input_tokens,
                output_tokens=output.output_tokens,
                latency_ms=output.latency_ms,
            ))
        except Exception as exc:
            results.append(BatchItemResponseV2(
                content=f"Error: {exc}",
                agent_name=agent.name,
            ))

    return results

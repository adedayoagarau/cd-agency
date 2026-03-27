"""Agent endpoints — run agents, list agents, and score content."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.cloud.api.deps import CurrentUser, get_current_user, get_db
from packages.cloud.database import UsageRecordCRUD

router = APIRouter(prefix="/v2/agents", tags=["agents"])


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class AgentRunRequest(BaseModel):
    agent_slug: str = Field(..., description="Slug of the agent to run, e.g. 'error'")
    input: str = Field(..., description="Content to send to the agent")
    project_id: str | None = Field(default=None, description="Optional project context")


class AgentRunResponse(BaseModel):
    run_id: str
    agent_slug: str
    output: str
    tokens_used: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentSummary(BaseModel):
    slug: str
    name: str
    description: str
    tags: list[str] = Field(default_factory=list)


class AgentDetail(AgentSummary):
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    related_agents: list[str] = Field(default_factory=list)
    system_prompt_preview: str = ""


class ScoreRequest(BaseModel):
    input: str = Field(..., description="Content to score")
    tools: list[str] = Field(
        default_factory=lambda: ["readability", "lint", "a11y"],
        description="Scoring tools to run",
    )


class ScoreResponse(BaseModel):
    scores: dict[str, Any]
    summary: str = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _check_usage_limit(
    user: CurrentUser, db: AsyncSession
) -> None:
    """Raise 429 if the organisation has exceeded its plan limits."""
    usage = await UsageRecordCRUD.get_current_period_usage(db, org_id=user.org_id)
    if usage and usage.get("limit_reached"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Usage limit reached for the current billing period. Please upgrade your plan.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_200_OK)
async def run_agent(
    body: AgentRunRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AgentRunResponse:
    """Run a content-design agent on the provided input."""
    await _check_usage_limit(user, db)

    # Lazy-import the runtime to avoid circular deps at module level
    from runtime.registry import AgentRegistry
    from runtime.runner import run_agent as execute_agent

    agent = AgentRegistry.get(body.agent_slug)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{body.agent_slug}' not found.",
        )

    result = await execute_agent(
        agent_slug=body.agent_slug,
        input_text=body.input,
        project_id=body.project_id,
    )

    # Record usage
    await UsageRecordCRUD.record(
        db,
        org_id=user.org_id,
        user_id=user.user_id,
        agent_slug=body.agent_slug,
        tokens=result.get("tokens_used", 0),
    )
    await db.commit()

    return AgentRunResponse(
        run_id=result["run_id"],
        agent_slug=body.agent_slug,
        output=result["output"],
        tokens_used=result.get("tokens_used", 0),
        metadata=result.get("metadata", {}),
    )


@router.get("", response_model=list[AgentSummary])
async def list_agents(
    user: CurrentUser = Depends(get_current_user),
) -> list[AgentSummary]:
    """List all available content-design agents."""
    from runtime.registry import AgentRegistry

    agents = AgentRegistry.list_all()
    return [
        AgentSummary(
            slug=a["slug"],
            name=a["name"],
            description=a.get("description", ""),
            tags=a.get("tags", []),
        )
        for a in agents
    ]


@router.get("/{slug}", response_model=AgentDetail)
async def get_agent(
    slug: str,
    user: CurrentUser = Depends(get_current_user),
) -> AgentDetail:
    """Get detailed information about a specific agent."""
    from runtime.registry import AgentRegistry

    agent = AgentRegistry.get(slug)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{slug}' not found.",
        )

    return AgentDetail(
        slug=agent["slug"],
        name=agent["name"],
        description=agent.get("description", ""),
        tags=agent.get("tags", []),
        inputs=agent.get("inputs", []),
        outputs=agent.get("outputs", []),
        related_agents=agent.get("related_agents", []),
        system_prompt_preview=agent.get("system_prompt_preview", ""),
    )


@router.post("/score", response_model=ScoreResponse, status_code=status.HTTP_200_OK)
async def score_content(
    body: ScoreRequest,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScoreResponse:
    """Run scoring tools (readability, lint, a11y) on the provided content."""
    await _check_usage_limit(user, db)

    from tools.readability import score as readability_score
    from tools.linter import lint as lint_score
    from tools.a11y import check as a11y_check

    scores: dict[str, Any] = {}

    if "readability" in body.tools:
        scores["readability"] = readability_score(body.input)
    if "lint" in body.tools:
        scores["lint"] = lint_score(body.input)
    if "a11y" in body.tools:
        scores["a11y"] = a11y_check(body.input)

    return ScoreResponse(
        scores=scores,
        summary=f"Ran {len(scores)} scoring tool(s).",
    )

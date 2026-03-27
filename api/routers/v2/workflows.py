"""V2 Workflow endpoints — list, detail, and run multi-agent pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.deps import get_registry, get_runner_with_user_key
from runtime.runner import AgentRunner
from runtime.workflow import WorkflowEngine, load_workflows_from_directory

router = APIRouter(prefix="/api/v2/workflows", tags=["workflows-v2"])

WORKFLOWS_DIR = Path(__file__).parent.parent.parent.parent / "workflows"


# ── Models ───────────────────────────────────────────────────────────────────


class WorkflowStepSchemaV2(BaseModel):
    name: str
    agent: str
    parallel_group: str | None = None
    condition: str | None = None


class WorkflowSummaryV2(BaseModel):
    slug: str
    name: str
    description: str
    step_count: int


class WorkflowDetailV2(BaseModel):
    slug: str
    name: str
    description: str
    steps: list[WorkflowStepSchemaV2]


class WorkflowRunRequestV2(BaseModel):
    input: dict[str, Any] = Field(..., description="Workflow input fields")


class StepResultResponseV2(BaseModel):
    step_name: str
    agent_name: str
    output: str
    skipped: bool = False
    error: str | None = None


class WorkflowRunResponseV2(BaseModel):
    workflow_name: str
    steps: list[StepResultResponseV2]
    final_output: str
    total_tokens: int = 0
    latency_ms: float = 0.0


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_all():
    return load_workflows_from_directory(WORKFLOWS_DIR)


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("", response_model=list[WorkflowSummaryV2])
async def list_workflows() -> list[WorkflowSummaryV2]:
    """List all available workflows."""
    try:
        workflows = _load_all()
        return [
            WorkflowSummaryV2(
                slug=w.slug,
                name=w.name,
                description=w.description,
                step_count=len(w.steps),
            )
            for w in workflows
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load workflows: {exc}",
        )


@router.get("/{slug}", response_model=WorkflowDetailV2)
async def get_workflow(slug: str) -> WorkflowDetailV2:
    """Get full details for a workflow by slug."""
    workflows = _load_all()
    for w in workflows:
        if w.slug == slug:
            return WorkflowDetailV2(
                slug=w.slug,
                name=w.name,
                description=w.description,
                steps=[
                    WorkflowStepSchemaV2(
                        name=s.name,
                        agent=s.agent,
                        parallel_group=s.parallel_group,
                        condition=s.condition,
                    )
                    for s in w.steps
                ],
            )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Workflow '{slug}' not found",
    )


@router.post("/{slug}/run", response_model=WorkflowRunResponseV2)
async def run_workflow(
    slug: str,
    body: WorkflowRunRequestV2,
    runner: Annotated[AgentRunner, Depends(get_runner_with_user_key)],
) -> WorkflowRunResponseV2:
    """Execute a multi-agent workflow with the given input."""
    workflows = _load_all()
    workflow = None
    for w in workflows:
        if w.slug == slug:
            workflow = w
            break

    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow '{slug}' not found",
        )

    registry = get_registry()
    config = runner.config

    engine = WorkflowEngine(registry=registry, runner=runner, config=config)

    try:
        result = engine.run(workflow, body.input)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {exc}",
        )

    step_responses = [
        StepResultResponseV2(
            step_name=sr.step_name,
            agent_name=sr.agent_name,
            output=sr.output.content if sr.output else "",
            skipped=sr.skipped,
            error=sr.error,
        )
        for sr in result.step_results
    ]

    token_totals = result.total_tokens

    return WorkflowRunResponseV2(
        workflow_name=workflow.name,
        steps=step_responses,
        final_output=result.final_output,
        total_tokens=token_totals.get("total", 0),
        latency_ms=result.total_latency_ms,
    )

"""Workflow endpoints — list, detail, and run multi-agent pipelines."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from api.deps import get_registry, get_runner_with_user_key, verify_api_key
from api.models import (
    StepResultResponse,
    WorkflowDetail,
    WorkflowRunRequest,
    WorkflowRunResponse,
    WorkflowStepSchema,
    WorkflowSummary,
)
from runtime.runner import AgentRunner
from runtime.workflow import WorkflowEngine, load_workflow, load_workflows_from_directory

from pathlib import Path

router = APIRouter(prefix="/workflows", tags=["workflows"])

WORKFLOWS_DIR = Path(__file__).parent.parent.parent / "workflows"


def _load_all():
    return load_workflows_from_directory(WORKFLOWS_DIR)


@router.get("", response_model=list[WorkflowSummary])
async def list_workflows(
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> list[WorkflowSummary]:
    """List all available workflows."""
    workflows = _load_all()
    return [
        WorkflowSummary(
            slug=w.slug,
            name=w.name,
            description=w.description,
            step_count=len(w.steps),
        )
        for w in workflows
    ]


@router.get("/{slug}", response_model=WorkflowDetail)
async def get_workflow(
    slug: str,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> WorkflowDetail:
    """Get full details for a workflow by slug."""
    workflows = _load_all()
    for w in workflows:
        if w.slug == slug:
            return WorkflowDetail(
                slug=w.slug,
                name=w.name,
                description=w.description,
                steps=[
                    WorkflowStepSchema(
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


@router.post("/{slug}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    slug: str,
    body: WorkflowRunRequest,
    runner: Annotated[AgentRunner, Depends(get_runner_with_user_key)],
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> WorkflowRunResponse:
    """Execute a multi-agent workflow with the given input."""
    from api.deps import get_registry

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
        StepResultResponse(
            step_name=sr.step_name,
            agent_name=sr.agent_name,
            output=sr.output.content if sr.output else "",
            skipped=sr.skipped,
            error=sr.error,
        )
        for sr in result.step_results
    ]

    token_totals = result.total_tokens

    return WorkflowRunResponse(
        workflow_name=workflow.name,
        steps=step_responses,
        final_output=result.final_output,
        total_tokens=token_totals.get("total", 0),
        latency_ms=result.total_latency_ms,
    )

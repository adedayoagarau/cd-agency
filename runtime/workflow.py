"""Workflow engine — executes multi-agent pipelines."""

from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from runtime.agent import AgentOutput
from runtime.config import Config
from runtime.registry import AgentRegistry
from runtime.runner import AgentRunner


@dataclass
class WorkflowStep:
    """A single step in a workflow pipeline."""

    name: str
    agent: str
    input_map: dict[str, str]
    output_key: str
    parallel_group: str | None = None
    condition: str | None = None


@dataclass
class StepResult:
    """Result from executing a single workflow step."""

    step_name: str
    agent_name: str
    output: AgentOutput
    skipped: bool = False
    error: str | None = None


@dataclass
class Workflow:
    """A multi-agent workflow definition."""

    name: str
    description: str
    steps: list[WorkflowStep]
    source_file: str = ""

    @property
    def slug(self) -> str:
        if self.source_file:
            return Path(self.source_file).stem
        return self.name.lower().replace(" ", "-")


@dataclass
class WorkflowResult:
    """Complete result from a workflow execution."""

    workflow_name: str
    step_results: list[StepResult] = field(default_factory=list)
    total_latency_ms: float = 0.0

    @property
    def final_output(self) -> str:
        """The content from the last executed (non-skipped) step."""
        for result in reversed(self.step_results):
            if not result.skipped and result.output:
                return result.output.content
        return ""

    @property
    def all_outputs(self) -> dict[str, str]:
        """Map of step_name → content for all executed steps."""
        return {
            r.step_name: r.output.content
            for r in self.step_results
            if not r.skipped and r.output
        }

    @property
    def total_tokens(self) -> dict[str, int]:
        """Aggregate token usage across all steps."""
        input_tokens = sum(r.output.input_tokens for r in self.step_results if r.output)
        output_tokens = sum(r.output.output_tokens for r in self.step_results if r.output)
        return {"input": input_tokens, "output": output_tokens, "total": input_tokens + output_tokens}


def load_workflow(filepath: Path) -> Workflow:
    """Load a workflow definition from a YAML file."""
    text = filepath.read_text(encoding="utf-8")
    data = yaml.safe_load(text)

    steps = []
    for step_data in data.get("steps", []):
        steps.append(WorkflowStep(
            name=step_data["name"],
            agent=step_data["agent"],
            input_map=step_data.get("input_map", {}),
            output_key=step_data.get("output_key", step_data["name"]),
            parallel_group=step_data.get("parallel_group"),
            condition=step_data.get("condition"),
        ))

    return Workflow(
        name=data.get("name", filepath.stem),
        description=data.get("description", ""),
        steps=steps,
        source_file=str(filepath),
    )


def load_workflows_from_directory(directory: Path) -> list[Workflow]:
    """Load all workflow YAML files from a directory, excluding schema.yaml."""
    workflows = []
    if not directory.exists():
        return workflows

    for filepath in sorted(directory.glob("*.yaml")):
        if filepath.name == "schema.yaml":
            continue
        try:
            workflow = load_workflow(filepath)
            workflows.append(workflow)
        except Exception as e:
            print(f"Warning: Failed to load workflow {filepath.name}: {e}")

    return workflows


class WorkflowEngine:
    """Executes multi-agent workflows."""

    def __init__(
        self,
        registry: AgentRegistry,
        runner: AgentRunner | None = None,
        config: Config | None = None,
        on_step_start: Any = None,
        on_step_complete: Any = None,
    ) -> None:
        self.registry = registry
        self.config = config or Config.from_env()
        self.runner = runner or AgentRunner(self.config)
        self.on_step_start = on_step_start
        self.on_step_complete = on_step_complete

    def run(self, workflow: Workflow, workflow_input: dict[str, Any]) -> WorkflowResult:
        """Execute a workflow synchronously.

        Steps run sequentially unless they share a parallel_group,
        in which case they run concurrently within that group.
        """
        start = time.monotonic()
        result = WorkflowResult(workflow_name=workflow.name)

        # Track outputs from completed steps
        step_outputs: dict[str, AgentOutput] = {}

        # Group steps by execution order
        step_groups = self._group_steps(workflow.steps)

        for group in step_groups:
            if len(group) == 1:
                # Sequential step
                step_result = self._execute_step(
                    group[0], workflow_input, step_outputs
                )
                result.step_results.append(step_result)
                if not step_result.skipped and step_result.output:
                    step_outputs[group[0].output_key] = step_result.output
            else:
                # Parallel group — run concurrently
                group_results = self._execute_parallel(
                    group, workflow_input, step_outputs
                )
                for step, step_result in zip(group, group_results):
                    result.step_results.append(step_result)
                    if not step_result.skipped and step_result.output:
                        step_outputs[step.output_key] = step_result.output

        result.total_latency_ms = (time.monotonic() - start) * 1000
        return result

    def _execute_step(
        self,
        step: WorkflowStep,
        workflow_input: dict[str, Any],
        step_outputs: dict[str, AgentOutput],
    ) -> StepResult:
        """Execute a single workflow step."""
        # Check condition
        if step.condition and not self._evaluate_condition(
            step.condition, workflow_input, step_outputs
        ):
            return StepResult(
                step_name=step.name,
                agent_name=step.agent,
                output=AgentOutput(content="", agent_name=step.agent),
                skipped=True,
            )

        # Resolve agent
        agent = self.registry.get(step.agent)
        if not agent:
            return StepResult(
                step_name=step.name,
                agent_name=step.agent,
                output=AgentOutput(content="", agent_name=step.agent),
                error=f"Agent not found: {step.agent}",
            )

        # Build input by resolving references
        resolved_input = self._resolve_input_map(
            step.input_map, workflow_input, step_outputs
        )

        if self.on_step_start:
            self.on_step_start(step.name, agent.name)

        try:
            output = self.runner.run(agent, resolved_input)
            step_result = StepResult(
                step_name=step.name,
                agent_name=agent.name,
                output=output,
            )
        except Exception as e:
            step_result = StepResult(
                step_name=step.name,
                agent_name=agent.name,
                output=AgentOutput(content="", agent_name=agent.name),
                error=str(e),
            )

        if self.on_step_complete:
            self.on_step_complete(step.name, step_result)

        return step_result

    def _execute_parallel(
        self,
        steps: list[WorkflowStep],
        workflow_input: dict[str, Any],
        step_outputs: dict[str, AgentOutput],
    ) -> list[StepResult]:
        """Execute multiple steps concurrently using threads."""
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=len(steps)) as executor:
            futures = [
                executor.submit(self._execute_step, step, workflow_input, step_outputs)
                for step in steps
            ]
            return [f.result() for f in futures]

    def _resolve_input_map(
        self,
        input_map: dict[str, str],
        workflow_input: dict[str, Any],
        step_outputs: dict[str, AgentOutput],
    ) -> dict[str, Any]:
        """Resolve $input and $steps references in the input map."""
        resolved: dict[str, Any] = {}

        for field_name, source in input_map.items():
            resolved[field_name] = self._resolve_reference(
                source, workflow_input, step_outputs
            )

        return resolved

    def _resolve_reference(
        self,
        source: str,
        workflow_input: dict[str, Any],
        step_outputs: dict[str, AgentOutput],
    ) -> Any:
        """Resolve a single reference string.

        Formats:
          $input.<field> — workflow input field
          $steps.<step_name>.content — previous step's output content
          $steps.<step_name>.<field> — previous step's output field
          anything else — literal string
        """
        if not isinstance(source, str):
            return source

        # $input.<field>
        match = re.match(r"^\$input\.(\w+)$", source)
        if match:
            return workflow_input.get(match.group(1), "")

        # $steps.<step>.<field>
        match = re.match(r"^\$steps\.(\w+)\.(\w+)$", source)
        if match:
            step_key = match.group(1)
            field_name = match.group(2)
            step_output = step_outputs.get(step_key)
            if step_output:
                if field_name == "content":
                    return step_output.content
                return getattr(step_output, field_name, "")
            return ""

        # Literal value (but inline $steps references in multiline strings)
        resolved = source
        for key, output in step_outputs.items():
            resolved = resolved.replace(f"$steps.{key}.content", output.content)
        return resolved

    def _group_steps(self, steps: list[WorkflowStep]) -> list[list[WorkflowStep]]:
        """Group steps by parallel_group. Sequential steps get their own group."""
        groups: list[list[WorkflowStep]] = []
        current_parallel: str | None = None
        current_group: list[WorkflowStep] = []

        for step in steps:
            if step.parallel_group:
                if step.parallel_group == current_parallel:
                    current_group.append(step)
                else:
                    if current_group:
                        groups.append(current_group)
                    current_parallel = step.parallel_group
                    current_group = [step]
            else:
                if current_group:
                    groups.append(current_group)
                    current_group = []
                    current_parallel = None
                groups.append([step])

        if current_group:
            groups.append(current_group)

        return groups

    def _evaluate_condition(
        self,
        condition: str,
        workflow_input: dict[str, Any],
        step_outputs: dict[str, AgentOutput],
    ) -> bool:
        """Evaluate a condition string. Returns True if the step should run."""
        try:
            return bool(eval(condition, {"__builtins__": {}}, {
                "input": workflow_input,
                "steps": {k: v.content for k, v in step_outputs.items()},
            }))
        except Exception:
            return False

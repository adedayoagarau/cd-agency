"""Tests for the workflow engine."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.config import Config
from runtime.registry import AgentRegistry
from runtime.runner import AgentRunner
from runtime.workflow import (
    Workflow,
    WorkflowEngine,
    WorkflowStep,
    WorkflowResult,
    load_workflow,
    load_workflows_from_directory,
)

WORKFLOWS_DIR = Path(__file__).parent.parent / "workflows"
AGENTS_DIR = Path(__file__).parent.parent / "content-design"


# --- Fixtures ---

def _make_agent(name: str, slug_file: str) -> Agent:
    return Agent(
        name=name,
        description=f"Test {name}",
        inputs=[AgentInput(name="content", type="string", required=True, description="Input")],
        system_prompt=f"You are {name}.",
        source_file=f"content-design/{slug_file}.md",
    )


def _mock_runner() -> AgentRunner:
    """Create a runner with a mocked client that returns predictable output."""
    runner = MagicMock(spec=AgentRunner)

    def fake_run(agent, user_input, **kwargs):
        return AgentOutput(
            content=f"Output from {agent.name}: {list(user_input.values())[0] if user_input else 'empty'}",
            agent_name=agent.name,
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            latency_ms=100.0,
        )

    runner.run.side_effect = fake_run
    return runner


# --- Workflow Loading ---

class TestLoadWorkflow:
    def test_loads_content_audit(self):
        wf = load_workflow(WORKFLOWS_DIR / "content-audit.yaml")
        assert wf.name == "Full Content Audit"
        assert len(wf.steps) == 4
        assert wf.steps[0].agent == "generalist"
        assert wf.steps[0].output_key == "generalist_result"

    def test_loads_error_pipeline(self):
        wf = load_workflow(WORKFLOWS_DIR / "error-message-pipeline.yaml")
        assert wf.name == "Error Message Pipeline"
        assert len(wf.steps) == 4
        assert wf.steps[0].agent == "error"

    def test_loads_launch_content(self):
        wf = load_workflow(WORKFLOWS_DIR / "launch-content-package.yaml")
        assert wf.name == "Launch Content Package"
        # First 3 steps should be parallel
        assert wf.steps[0].parallel_group == "launch_content"
        assert wf.steps[1].parallel_group == "launch_content"
        assert wf.steps[2].parallel_group == "launch_content"
        # Last step is sequential (no parallel group)
        assert wf.steps[3].parallel_group is None

    def test_loads_localization_prep(self):
        wf = load_workflow(WORKFLOWS_DIR / "localization-prep.yaml")
        assert wf.name == "Localization Prep"
        assert len(wf.steps) == 3

    def test_loads_notification_suite(self):
        wf = load_workflow(WORKFLOWS_DIR / "notification-suite.yaml")
        assert wf.name == "Notification Suite"
        assert len(wf.steps) == 4

    def test_workflow_slug(self):
        wf = load_workflow(WORKFLOWS_DIR / "content-audit.yaml")
        assert wf.slug == "content-audit"


class TestLoadWorkflowsFromDirectory:
    def test_loads_all_workflows(self):
        workflows = load_workflows_from_directory(WORKFLOWS_DIR)
        assert len(workflows) == 5  # 5 workflow files (excluding schema.yaml)

    def test_excludes_schema(self):
        workflows = load_workflows_from_directory(WORKFLOWS_DIR)
        slugs = [w.slug for w in workflows]
        assert "schema" not in slugs

    def test_nonexistent_directory(self):
        workflows = load_workflows_from_directory(Path("/nonexistent"))
        assert workflows == []


# --- Workflow Engine ---

class TestWorkflowEngine:
    def test_sequential_execution(self):
        """Steps run in order, each receiving previous outputs."""
        registry = AgentRegistry([
            _make_agent("Agent A", "agent-a"),
            _make_agent("Agent B", "agent-b"),
        ])
        registry.add_alias("agent-a", "agent-a")
        registry.add_alias("agent-b", "agent-b")

        workflow = Workflow(
            name="Test Sequential",
            description="Test",
            steps=[
                WorkflowStep(
                    name="step_a",
                    agent="agent-a",
                    input_map={"content": "$input.text"},
                    output_key="result_a",
                ),
                WorkflowStep(
                    name="step_b",
                    agent="agent-b",
                    input_map={"content": "$steps.result_a.content"},
                    output_key="result_b",
                ),
            ],
        )

        runner = _mock_runner()
        engine = WorkflowEngine(registry, runner=runner)
        result = engine.run(workflow, {"text": "Hello world"})

        assert len(result.step_results) == 2
        assert not result.step_results[0].skipped
        assert not result.step_results[1].skipped
        assert "Agent A" in result.step_results[0].output.content
        assert "Agent B" in result.step_results[1].output.content
        # Step B should have received Step A's output
        call_args = runner.run.call_args_list[1]
        step_b_input = call_args[0][1]  # second positional arg = user_input
        assert "Output from Agent A" in step_b_input["content"]

    def test_parallel_execution(self):
        """Steps in the same parallel group run concurrently."""
        registry = AgentRegistry([
            _make_agent("Agent A", "agent-a"),
            _make_agent("Agent B", "agent-b"),
            _make_agent("Agent C", "agent-c"),
        ])
        registry.add_alias("agent-a", "agent-a")
        registry.add_alias("agent-b", "agent-b")
        registry.add_alias("agent-c", "agent-c")

        workflow = Workflow(
            name="Test Parallel",
            description="Test",
            steps=[
                WorkflowStep(
                    name="step_a", agent="agent-a",
                    input_map={"content": "$input.text"},
                    output_key="result_a", parallel_group="group1",
                ),
                WorkflowStep(
                    name="step_b", agent="agent-b",
                    input_map={"content": "$input.text"},
                    output_key="result_b", parallel_group="group1",
                ),
                WorkflowStep(
                    name="step_c", agent="agent-c",
                    input_map={"content": "$input.text"},
                    output_key="result_c",
                ),
            ],
        )

        runner = _mock_runner()
        engine = WorkflowEngine(registry, runner=runner)
        result = engine.run(workflow, {"text": "Hello"})

        assert len(result.step_results) == 3
        assert runner.run.call_count == 3

    def test_conditional_skip(self):
        """Steps with unmet conditions are skipped."""
        registry = AgentRegistry([_make_agent("Agent A", "agent-a")])
        registry.add_alias("agent-a", "agent-a")

        workflow = Workflow(
            name="Test Conditional",
            description="Test",
            steps=[
                WorkflowStep(
                    name="step_a", agent="agent-a",
                    input_map={"content": "$input.text"},
                    output_key="result_a",
                    condition="False",  # Always skip
                ),
            ],
        )

        runner = _mock_runner()
        engine = WorkflowEngine(registry, runner=runner)
        result = engine.run(workflow, {"text": "Hello"})

        assert len(result.step_results) == 1
        assert result.step_results[0].skipped
        assert runner.run.call_count == 0  # Agent never called

    def test_missing_agent_error(self):
        """Steps referencing unknown agents produce an error result."""
        registry = AgentRegistry()

        workflow = Workflow(
            name="Test Missing",
            description="Test",
            steps=[
                WorkflowStep(
                    name="step_a", agent="nonexistent",
                    input_map={"content": "$input.text"},
                    output_key="result_a",
                ),
            ],
        )

        runner = _mock_runner()
        engine = WorkflowEngine(registry, runner=runner)
        result = engine.run(workflow, {"text": "Hello"})

        assert result.step_results[0].error == "Agent not found: nonexistent"


class TestWorkflowResult:
    def test_final_output(self):
        result = WorkflowResult(
            workflow_name="Test",
            step_results=[
                MagicMock(skipped=False, output=MagicMock(content="First")),
                MagicMock(skipped=False, output=MagicMock(content="Second")),
            ],
        )
        assert result.final_output == "Second"

    def test_final_output_skips_skipped(self):
        result = WorkflowResult(
            workflow_name="Test",
            step_results=[
                MagicMock(skipped=False, output=MagicMock(content="First")),
                MagicMock(skipped=True, output=None),
            ],
        )
        assert result.final_output == "First"

    def test_all_outputs(self):
        result = WorkflowResult(
            workflow_name="Test",
            step_results=[
                MagicMock(skipped=False, step_name="a", output=MagicMock(content="Output A")),
                MagicMock(skipped=False, step_name="b", output=MagicMock(content="Output B")),
            ],
        )
        outputs = result.all_outputs
        assert outputs["a"] == "Output A"
        assert outputs["b"] == "Output B"

    def test_total_tokens(self):
        result = WorkflowResult(
            workflow_name="Test",
            step_results=[
                MagicMock(output=MagicMock(input_tokens=100, output_tokens=50)),
                MagicMock(output=MagicMock(input_tokens=200, output_tokens=80)),
            ],
        )
        tokens = result.total_tokens
        assert tokens["input"] == 300
        assert tokens["output"] == 130
        assert tokens["total"] == 430


class TestInputResolution:
    def test_resolves_workflow_input(self):
        registry = AgentRegistry([_make_agent("Agent A", "agent-a")])
        registry.add_alias("agent-a", "agent-a")

        workflow = Workflow(
            name="Test",
            description="Test",
            steps=[
                WorkflowStep(
                    name="step_a", agent="agent-a",
                    input_map={"content": "$input.my_content"},
                    output_key="result_a",
                ),
            ],
        )

        runner = _mock_runner()
        engine = WorkflowEngine(registry, runner=runner)
        engine.run(workflow, {"my_content": "Hello from input"})

        call_args = runner.run.call_args_list[0]
        assert call_args[0][1]["content"] == "Hello from input"

    def test_resolves_literal_value(self):
        registry = AgentRegistry([_make_agent("Agent A", "agent-a")])
        registry.add_alias("agent-a", "agent-a")

        workflow = Workflow(
            name="Test",
            description="Test",
            steps=[
                WorkflowStep(
                    name="step_a", agent="agent-a",
                    input_map={"content": "A literal string value"},
                    output_key="result_a",
                ),
            ],
        )

        runner = _mock_runner()
        engine = WorkflowEngine(registry, runner=runner)
        engine.run(workflow, {})

        call_args = runner.run.call_args_list[0]
        assert call_args[0][1]["content"] == "A literal string value"


class TestWorkflowEngineWithRealAgents:
    """Test that workflows resolve agents from the real agent directory."""

    def test_content_audit_agents_resolve(self):
        """All agents in the content audit workflow exist in the registry."""
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        wf = load_workflow(WORKFLOWS_DIR / "content-audit.yaml")

        for step in wf.steps:
            agent = registry.get(step.agent)
            assert agent is not None, f"Agent '{step.agent}' not found for step '{step.name}'"

    def test_all_workflow_agents_resolve(self):
        """Every agent referenced by any workflow exists in the registry."""
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        workflows = load_workflows_from_directory(WORKFLOWS_DIR)

        for wf in workflows:
            for step in wf.steps:
                agent = registry.get(step.agent)
                assert agent is not None, (
                    f"Workflow '{wf.name}', step '{step.name}': "
                    f"agent '{step.agent}' not found in registry"
                )

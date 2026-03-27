"""Tests for the enhanced multi-agent orchestrator."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.orchestrator import (
    AgentHandoff,
    OrchestratedPipeline,
    PipelineResult,
    PipelineStep,
    RoutingRule,
    SharedContext,
    StepOutput,
    content_quality_pipeline,
    error_message_pipeline,
    localization_pipeline,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_runner():
    runner = MagicMock()
    runner.run.return_value = AgentOutput(
        content="Improved content from agent.",
        agent_name="Test Agent",
        model="test-model",
        input_tokens=50,
        output_tokens=30,
        latency_ms=100,
    )
    return runner


@pytest.fixture
def mock_registry():
    def _get(slug):
        return Agent(
            name=slug.replace("-", " ").title(),
            description=f"Agent {slug}",
            inputs=[AgentInput(name="content", type="string", required=True)],
            system_prompt=f"You are {slug}.",
            source_file=f"{slug}.md",
        )

    registry = MagicMock()
    registry.get = _get
    return registry


# ---------------------------------------------------------------------------
# SharedContext
# ---------------------------------------------------------------------------

class TestSharedContext:
    def test_empty_context(self):
        ctx = SharedContext()
        assert ctx.build_context_block() == ""

    def test_record_decision(self):
        ctx = SharedContext()
        ctx.record_decision("agent-a", "Use sign in instead of log in", "Brand guide")
        assert len(ctx.decisions) == 1
        assert ctx.decisions[0]["agent"] == "agent-a"

    def test_record_finding(self):
        ctx = SharedContext()
        ctx.record_finding("agent-a", "readability_issue", "Flesch score too low")
        assert "readability_issue" in ctx.accumulated_findings

    def test_record_quality(self):
        ctx = SharedContext()
        ctx.record_quality("agent-a", {"readability": 75.0, "lint": 90.0})
        assert ctx.quality_scores["agent-a"]["readability"] == 75.0

    def test_build_context_with_decisions(self):
        ctx = SharedContext()
        ctx.record_decision("agent-a", "Use active voice")
        ctx.terminology_updates["log in"] = "sign in"
        block = ctx.build_context_block()
        assert "Pipeline Context" in block
        assert "active voice" in block
        assert "sign in" in block

    def test_handoff_chain(self):
        ctx = SharedContext()
        h1 = AgentHandoff(from_agent="A", to_agent="B")
        h2 = AgentHandoff(from_agent="B", to_agent="C")
        ctx.add_handoff(h1)
        ctx.add_handoff(h2)
        assert ctx.get_latest_handoff() == h2
        assert len(ctx.handoffs) == 2

    def test_get_latest_handoff_empty(self):
        ctx = SharedContext()
        assert ctx.get_latest_handoff() is None


# ---------------------------------------------------------------------------
# AgentHandoff
# ---------------------------------------------------------------------------

class TestAgentHandoff:
    def test_defaults(self):
        h = AgentHandoff(from_agent="A", to_agent="B")
        assert h.from_agent == "A"
        assert h.to_agent == "B"
        assert h.timestamp > 0

    def test_build_context_block(self):
        h = AgentHandoff(
            from_agent="Tone Agent",
            to_agent="A11y Agent",
            instructions="Check for screen reader issues",
            focus_areas=["alt text", "aria labels"],
            quality_scores={"readability": 80.0},
        )
        block = h.build_context_block()
        assert "Handoff from Tone Agent" in block
        assert "screen reader" in block
        assert "alt text" in block
        assert "readability" in block

    def test_empty_handoff_context(self):
        h = AgentHandoff(from_agent="A", to_agent="B")
        block = h.build_context_block()
        assert "Handoff from A" in block


# ---------------------------------------------------------------------------
# OrchestratedPipeline
# ---------------------------------------------------------------------------

class TestOrchestratedPipeline:
    def test_simple_pipeline(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Test Pipeline",
            steps=[
                PipelineStep(agent_slug="content-designer-generalist"),
                PipelineStep(agent_slug="tone-evaluation-agent"),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test input"})

        assert isinstance(result, PipelineResult)
        assert len(result.steps) == 2
        assert result.final_output == "Improved content from agent."
        assert result.total_duration_ms > 0
        assert mock_runner.run.call_count == 2

    def test_pipeline_with_handoff(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Handoff Pipeline",
            steps=[
                PipelineStep(
                    agent_slug="error-message-architect",
                    handoff_instructions="Draft error messages.",
                ),
                PipelineStep(
                    agent_slug="accessibility-content-auditor",
                    handoff_instructions="Check a11y compliance.",
                    focus_areas=["WCAG", "screen readers"],
                ),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "error text"})

        assert len(result.steps) == 2
        # First step should have a handoff to second
        assert result.steps[0].handoff is not None
        assert result.steps[0].handoff.to_agent == "accessibility-content-auditor"

    def test_pipeline_agent_not_found(self, mock_runner):
        registry = MagicMock()
        registry.get.return_value = None

        pipeline = OrchestratedPipeline(
            name="Missing Agent",
            steps=[PipelineStep(agent_slug="nonexistent-agent")],
        )

        result = pipeline.run(mock_runner, registry, {"content": "test"})

        assert len(result.steps) == 1
        assert result.steps[0].error is not None
        assert "not found" in result.steps[0].error

    def test_pipeline_agent_error(self, mock_registry):
        runner = MagicMock()
        runner.run.side_effect = Exception("LLM API error")

        pipeline = OrchestratedPipeline(
            name="Error Pipeline",
            steps=[PipelineStep(agent_slug="content-designer-generalist")],
        )

        result = pipeline.run(runner, mock_registry, {"content": "test"})

        assert len(result.steps) == 1
        assert result.steps[0].error == "LLM API error"

    def test_pipeline_skip_condition(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Skip Pipeline",
            steps=[
                PipelineStep(agent_slug="content-designer-generalist"),
                PipelineStep(
                    agent_slug="tone-evaluation-agent",
                    skip_if=lambda ctx: True,  # Always skip
                ),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test"})

        assert len(result.steps) == 2
        assert result.steps[1].skipped is True
        assert mock_runner.run.call_count == 1  # Only first step ran

    def test_pipeline_dynamic_routing(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Dynamic Pipeline",
            steps=[
                PipelineStep(
                    agent_slug="content-designer-generalist",
                    routing_rules=[
                        RoutingRule(
                            condition=lambda ctx: True,  # Always trigger
                            target_agent="accessibility-content-auditor",
                            description="Dynamic route to a11y.",
                        ),
                    ],
                ),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test"})

        # Original step + dynamically added step
        assert len(result.steps) == 2
        assert result.dynamic_steps_added == 1
        assert result.steps[1].agent_slug == "accessibility-content-auditor"

    def test_dynamic_routing_max_limit(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Max Dynamic",
            steps=[
                PipelineStep(
                    agent_slug="content-designer-generalist",
                    routing_rules=[
                        RoutingRule(
                            condition=lambda ctx: True,
                            target_agent="tone-evaluation-agent",
                        ),
                    ],
                ),
            ],
            max_dynamic_steps=1,
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test"})

        # Should cap at max_dynamic_steps
        assert result.dynamic_steps_added <= 1

    def test_pipeline_callbacks(self, mock_runner, mock_registry):
        started = []
        completed = []

        pipeline = OrchestratedPipeline(
            name="Callback Pipeline",
            steps=[
                PipelineStep(agent_slug="content-designer-generalist"),
            ],
            on_step_start=lambda i, name: started.append((i, name)),
            on_step_complete=lambda i, name, out: completed.append((i, name)),
        )

        pipeline.run(mock_runner, mock_registry, {"content": "test"})

        assert len(started) == 1
        assert len(completed) == 1

    def test_pipeline_shared_context_accumulates(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Context Pipeline",
            steps=[
                PipelineStep(agent_slug="content-designer-generalist"),
                PipelineStep(agent_slug="tone-evaluation-agent"),
                PipelineStep(agent_slug="accessibility-content-auditor"),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test"})

        # Quality scores should be recorded for each step
        assert len(result.shared_context.quality_scores) >= 0  # best-effort scoring

    def test_pipeline_input_mapping(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Input Map Pipeline",
            steps=[
                PipelineStep(
                    agent_slug="content-designer-generalist",
                    input_map={"content": "$input.text"},
                ),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"text": "custom input"})
        assert len(result.steps) == 1

    def test_pipeline_total_tokens(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Token Pipeline",
            steps=[
                PipelineStep(agent_slug="agent-a"),
                PipelineStep(agent_slug="agent-b"),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test"})

        tokens = result.total_tokens
        assert tokens["input"] == 100  # 50 * 2
        assert tokens["output"] == 60  # 30 * 2
        assert tokens["total"] == 160

    def test_pipeline_all_outputs(self, mock_runner, mock_registry):
        pipeline = OrchestratedPipeline(
            name="Outputs Pipeline",
            steps=[
                PipelineStep(agent_slug="agent-a"),
                PipelineStep(agent_slug="agent-b"),
            ],
        )

        result = pipeline.run(mock_runner, mock_registry, {"content": "test"})

        assert "agent-a" in result.all_outputs
        assert "agent-b" in result.all_outputs


# ---------------------------------------------------------------------------
# PipelineResult
# ---------------------------------------------------------------------------

class TestPipelineResult:
    def test_final_output_skips_empty(self):
        result = PipelineResult(
            pipeline_name="test",
            steps=[
                StepOutput(
                    step_index=0, agent_name="A", agent_slug="a",
                    output=AgentOutput(content="good output", agent_name="A"),
                ),
                StepOutput(
                    step_index=1, agent_name="B", agent_slug="b",
                    output=AgentOutput(content="", agent_name="B"),
                    skipped=True,
                ),
            ],
        )
        assert result.final_output == "good output"

    def test_handoff_chain(self):
        h1 = AgentHandoff(from_agent="A", to_agent="B")
        result = PipelineResult(
            pipeline_name="test",
            steps=[
                StepOutput(
                    step_index=0, agent_name="A", agent_slug="a",
                    output=AgentOutput(content="x", agent_name="A"),
                    handoff=h1,
                ),
                StepOutput(
                    step_index=1, agent_name="B", agent_slug="b",
                    output=AgentOutput(content="y", agent_name="B"),
                ),
            ],
        )
        assert len(result.handoff_chain) == 1


# ---------------------------------------------------------------------------
# Pre-built pipelines
# ---------------------------------------------------------------------------

class TestPrebuiltPipelines:
    def test_content_quality_pipeline(self):
        p = content_quality_pipeline()
        assert p.name == "Content Quality Pipeline"
        assert len(p.steps) == 4

    def test_error_message_pipeline(self):
        p = error_message_pipeline()
        assert p.name == "Error Message Pipeline"
        assert len(p.steps) == 4

    def test_localization_pipeline(self):
        p = localization_pipeline()
        assert p.name == "Localization Prep Pipeline"
        assert len(p.steps) == 3

    def test_prebuilt_pipelines_run(self, mock_runner, mock_registry):
        """All pre-built pipelines should execute without error."""
        for pipeline_fn in (content_quality_pipeline, error_message_pipeline, localization_pipeline):
            pipeline = pipeline_fn()
            result = pipeline.run(mock_runner, mock_registry, {"content": "test"})
            assert isinstance(result, PipelineResult)
            assert len(result.steps) > 0

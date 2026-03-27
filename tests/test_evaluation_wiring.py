"""Tests that evaluation data flows correctly from runner through API endpoints.

Verifies:
1. Agent with tools returns real evaluation scores (not empty dict)
2. Agent without tools still returns a valid response with post-hoc scores
3. WebSocket streaming returns evaluation data in the evaluation message
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.config import Config
from runtime.model_providers import ProviderResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def agent_with_tools() -> Agent:
    return Agent(
        name="Eval Test Agent",
        description="Agent with tools for evaluation testing",
        inputs=[AgentInput(name="content", type="string", required=True)],
        available_tools=["run_linter", "score_readability", "check_accessibility"],
        system_prompt="You are a test agent.",
        source_file="eval-test-agent.md",
    )


@pytest.fixture
def agent_without_tools() -> Agent:
    return Agent(
        name="Simple Test Agent",
        description="Agent without tools",
        inputs=[AgentInput(name="content", type="string", required=True)],
        available_tools=[],
        system_prompt="You are a simple test agent.",
        source_file="simple-test-agent.md",
    )


@pytest.fixture
def mock_config() -> Config:
    return Config(api_key="test-key", model="test-model")


def _mock_provider_response(content: str = "Click the button to continue.") -> ProviderResponse:
    return ProviderResponse(
        content=content,
        input_tokens=100,
        output_tokens=50,
        model="test-model",
    )


# ---------------------------------------------------------------------------
# Test 1: Agent with tools returns real evaluation scores
# ---------------------------------------------------------------------------

class TestAgentWithToolsEvaluation:
    """Running an agent via LangGraph populates evaluation fields from graph state."""

    def test_evaluate_node_produces_real_scores(self, agent_with_tools):
        """The evaluate node must populate evaluation_scores with real tool output."""
        from runtime.langgraph_agent import ContentDesignGraph, _normalize_evaluation_scores
        from runtime.tools.content_tools import RunLinter, ScoreReadability, CheckAccessibility
        from runtime.memory import ProjectMemory
        import tempfile
        from pathlib import Path

        tmp = tempfile.mkdtemp()
        memory = ProjectMemory(project_dir=Path(tmp))

        mock_router = MagicMock()

        tools = [RunLinter(), ScoreReadability(), CheckAccessibility()]

        graph = ContentDesignGraph(
            agent=agent_with_tools,
            tools=tools,
            model_router=mock_router,
            memory=memory,
            model="test-model",
            max_iterations=1,
        )

        # Directly invoke the evaluate node with real content
        state = {"current_output": "Try refreshing the page. Your changes have been saved."}
        result = graph._node_evaluate(state)

        scores = result["evaluation_scores"]
        assert "readability" in scores
        assert "linter" in scores
        assert "accessibility" in scores
        assert "_composite" in scores
        assert scores["_composite"] > 0

        # Verify normalization produces the right shape
        normalized = _normalize_evaluation_scores(scores)
        assert isinstance(normalized, dict)
        assert len(normalized) > 0
        assert "readability" in normalized
        assert all(isinstance(v, float) for v in normalized.values())
        assert all(0 <= v <= 100 for v in normalized.values())

    def test_posthoc_evaluation_returns_scores(self):
        """run_posthoc_evaluation must return non-empty scores for valid content."""
        from runtime.langgraph_agent import run_posthoc_evaluation

        evaluation, composite = run_posthoc_evaluation(
            "Click the button to continue. Your changes have been saved."
        )

        assert isinstance(evaluation, dict)
        assert len(evaluation) > 0, "Post-hoc evaluation must not be empty"
        assert "readability" in evaluation
        assert "linter" in evaluation
        assert isinstance(composite, float)
        assert composite > 0


# ---------------------------------------------------------------------------
# Test 2: Agent without tools returns valid response with post-hoc scores
# ---------------------------------------------------------------------------

class TestAgentWithoutToolsEvaluation:
    """Direct LLM path still produces evaluation via post-hoc scoring."""

    @patch("runtime.runner.ModelRouter.from_config")
    def test_direct_path_has_posthoc_evaluation(
        self, mock_from_config, agent_without_tools, mock_config
    ):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _mock_provider_response(
            "Click the button to save your work. This is a simple message."
        )
        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        from runtime.runner import AgentRunner

        runner = AgentRunner(mock_config)
        result = runner.run(agent_without_tools, {"content": "test input"})

        assert isinstance(result, AgentOutput)
        assert result.content == "Click the button to save your work. This is a simple message."
        assert isinstance(result.evaluation, dict)
        # Post-hoc evaluation should have at least readability and linter
        assert "readability" in result.evaluation
        assert "linter" in result.evaluation
        assert isinstance(result.composite_score, float)
        assert result.composite_score > 0
        assert isinstance(result.passed, bool)
        assert result.iterations == 1


# ---------------------------------------------------------------------------
# Test 3: WebSocket streaming returns evaluation data
# ---------------------------------------------------------------------------

class TestWebSocketEvaluationData:
    """WebSocket endpoint sends real evaluation in the evaluation message."""

    @pytest.mark.asyncio
    async def test_websocket_sends_real_evaluation(self, agent_with_tools):
        """The WS evaluation message must contain actual scores, not stubs."""
        from api.routers.v2.websocket import stream_agent_run

        # Build a mock AgentOutput with real evaluation data
        mock_output = AgentOutput(
            content="Your session has expired. Sign in again.",
            agent_name="Eval Test Agent",
            model="test-model",
            evaluation={"readability": 85.0, "linter": 90.0, "accessibility": 100.0},
            composite_score=91.67,
            passed=True,
            iterations=2,
            raw_response={"scores": {}, "council": None},
        )

        mock_ws = AsyncMock()
        mock_ws.receive_json = AsyncMock(return_value={
            "agent_slug": "eval-test-agent",
            "content": "test input",
            "anthropic_key": "test-key",
        })

        mock_runner = MagicMock()
        mock_runner.run.return_value = mock_output

        mock_agent = agent_with_tools

        # The websocket module imports inline, so patch at the source modules
        with patch("api.deps.get_registry") as mock_registry_fn, \
             patch("runtime.runner.AgentRunner") as mock_runner_cls, \
             patch("runtime.config.Config") as mock_config_cls:

            mock_registry = MagicMock()
            mock_registry.get.return_value = mock_agent
            mock_registry_fn.return_value = mock_registry
            mock_runner_cls.return_value = mock_runner
            mock_config_cls.from_env.return_value = MagicMock()

            await stream_agent_run(mock_ws)

        # Find the evaluation message among all send_json calls
        eval_msg = None
        for call in mock_ws.send_json.call_args_list:
            msg = call[0][0]
            if msg.get("type") == "evaluation":
                eval_msg = msg
                break

        assert eval_msg is not None, "WebSocket must send an evaluation message"
        assert eval_msg["evaluation"] == {"readability": 85.0, "linter": 90.0, "accessibility": 100.0}
        assert eval_msg["composite_score"] == 91.67
        assert eval_msg["passed"] is True
        assert eval_msg["iterations"] == 2

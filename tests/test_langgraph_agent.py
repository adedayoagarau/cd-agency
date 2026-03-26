"""Tests for the LangGraph agent runtime.

These tests mock the LLM and verify graph execution flow without
requiring langgraph to be installed — the graph logic is tested via
direct node-level calls and the availability check is tested separately.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.config import Config
from runtime.model_providers import ProviderResponse
from runtime.tools.base import ToolResult
from runtime.tools.content_tools import RunLinter, ScoreReadability, CheckAccessibility
from runtime.tools.memory_tools import RememberContext, RecallContext


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_agent() -> Agent:
    return Agent(
        name="Test Agent",
        description="A test agent with tools",
        inputs=[AgentInput(name="error_scenario", type="string", required=True)],
        available_tools=["run_linter", "score_readability", "check_accessibility",
                         "recall_context", "remember_context"],
        system_prompt="You are a content design agent.",
        source_file="test-agent.md",
    )


@pytest.fixture
def agent_no_tools() -> Agent:
    return Agent(
        name="Simple Agent",
        description="No tools",
        inputs=[AgentInput(name="content", type="string", required=True)],
        available_tools=[],
        system_prompt="You are simple.",
        source_file="simple-agent.md",
    )


@pytest.fixture
def mock_memory(tmp_path):
    from runtime.memory import ProjectMemory
    return ProjectMemory(project_dir=tmp_path)


@pytest.fixture
def mock_router():
    mock_provider = MagicMock()
    mock_response = ProviderResponse(
        content="Here is an improved error message. Try refreshing the page.",
        input_tokens=100,
        output_tokens=50,
        model="test-model",
    )
    mock_provider.complete.return_value = mock_response

    router = MagicMock()
    router.resolve.return_value = (mock_provider, "test-model")
    return router


# ---------------------------------------------------------------------------
# Agent state
# ---------------------------------------------------------------------------

class TestAgentState:
    def test_initial_state(self):
        from runtime.langgraph_agent import _initial_state

        state = _initial_state(
            agent_name="test",
            user_message="Fix this error",
            system_message="You are a test agent.",
            tools_available=["run_linter"],
            max_iterations=3,
        )
        assert state["agent_name"] == "test"
        assert len(state["messages"]) == 1
        assert state["iteration_count"] == 0
        assert state["max_iterations"] == 3
        assert state["final_output"] == ""


# ---------------------------------------------------------------------------
# ContentDesignGraph — node-level tests (no langgraph needed)
# ---------------------------------------------------------------------------

class TestContentDesignGraphNodes:
    def _make_graph(self, agent, mock_router, mock_memory):
        from runtime.langgraph_agent import ContentDesignGraph

        tools = [RunLinter(), ScoreReadability(), CheckAccessibility(),
                 RecallContext(memory=mock_memory), RememberContext(memory=mock_memory)]
        return ContentDesignGraph(
            agent=agent,
            tools=tools,
            model_router=mock_router,
            memory=mock_memory,
            model="test-model",
        )

    def test_retrieve_context_node(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {
            "messages": [{"role": "user", "content": "test query"}],
            "agent_name": "Test Agent",
        }
        result = graph._node_retrieve_context(state)
        assert "memory_context" in result

    def test_evaluate_node_scores(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {"current_output": "Click here to try again. This is a simple message."}
        result = graph._node_evaluate(state)
        scores = result["evaluation_scores"]
        assert "readability" in scores
        assert "linter" in scores
        assert "accessibility" in scores

    def test_finalize_stores_memory(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {"current_output": "Your session has expired. Sign in again to continue."}
        graph._node_finalize(state)
        # Should have stored something in memory
        assert len(mock_memory) >= 1

    def test_should_regenerate_below_threshold(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 30.0},
                "linter": {"issues": []},
            },
        }
        assert graph._should_regenerate(state) == "regenerate"

    def test_should_finalize_good_scores(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 80.0},
                "linter": {"issues": []},
            },
        }
        assert graph._should_regenerate(state) == "finalize"

    def test_should_finalize_max_iterations(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {
            "iteration_count": 3,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 20.0},
            },
        }
        assert graph._should_regenerate(state) == "finalize"

    def test_should_regenerate_lint_errors(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 80.0},
                "linter": {
                    "issues": [{"severity": "error", "message": "bad"}],
                },
            },
        }
        assert graph._should_regenerate(state) == "regenerate"

    def test_build_feedback(self, sample_agent, mock_router, mock_memory):
        graph = self._make_graph(sample_agent, mock_router, mock_memory)
        scores = {
            "readability": {"flesch_reading_ease": 40.0, "flesch_kincaid_grade": 14.0},
            "linter": {
                "issues": [
                    {"message": "Found jargon", "suggestion": "Use plain language", "severity": "warning"},
                ],
            },
            "accessibility": {
                "issues": [
                    {"wcag_criterion": "2.4.4", "message": "Click here pattern found"},
                ],
            },
        }
        feedback = graph._build_feedback(scores)
        assert "Readability" in feedback
        assert "Linter" in feedback
        assert "Accessibility" in feedback


# ---------------------------------------------------------------------------
# LangGraph availability check
# ---------------------------------------------------------------------------

class TestLangGraphAvailability:
    def test_availability_check_import(self):
        from runtime.langgraph_agent import langgraph_available
        # Returns bool — True if langgraph is installed, False otherwise
        result = langgraph_available()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Runner backward compatibility
# ---------------------------------------------------------------------------

class TestRunnerBackwardCompatibility:
    """Agents WITHOUT tools must still use the direct LLM call path."""

    @patch("runtime.runner.ModelRouter.from_config")
    def test_agent_without_tools_uses_direct_path(
        self, mock_from_config, agent_no_tools
    ):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = ProviderResponse(
            content="Direct response", input_tokens=10, output_tokens=5
        )
        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        from runtime.runner import AgentRunner

        config = Config(api_key="test-key", model="test-model")
        runner = AgentRunner(config)
        result = runner.run(agent_no_tools, {"content": "test"})

        assert result.content == "Direct response"
        # Provider.complete was called directly (not through LangGraph)
        mock_provider.complete.assert_called_once()

    @patch("runtime.runner.ModelRouter.from_config")
    def test_agent_with_tools_but_no_langgraph_falls_back(
        self, mock_from_config, sample_agent
    ):
        """If langgraph is not installed, agents with tools fall back to direct."""
        mock_provider = MagicMock()
        mock_provider.complete.return_value = ProviderResponse(
            content="Fallback response", input_tokens=10, output_tokens=5
        )
        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        from runtime.runner import AgentRunner

        config = Config(api_key="test-key", model="test-model")
        runner = AgentRunner(config)

        # Mock langgraph as unavailable
        with patch("runtime.runner.AgentRunner._try_langgraph_run", return_value=None):
            result = runner.run(sample_agent, {"error_scenario": "test error"})

        assert result.content == "Fallback response"


# ---------------------------------------------------------------------------
# Agent available_tools field
# ---------------------------------------------------------------------------

class TestAgentAvailableTools:
    def test_default_empty(self):
        agent = Agent(name="Test", description="test")
        assert agent.available_tools == []

    def test_set_tools(self):
        agent = Agent(
            name="Test", description="test",
            available_tools=["run_linter", "score_readability"],
        )
        assert len(agent.available_tools) == 2
        assert "run_linter" in agent.available_tools

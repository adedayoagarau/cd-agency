"""Tests for the AgentRunner (mocked, no real API calls)."""

from unittest.mock import MagicMock, patch

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.config import Config
from runtime.providers import CompletionResult
from runtime.runner import AgentRunner


@pytest.fixture
def mock_config() -> Config:
    return Config(api_key="test-key", model="test-model")


@pytest.fixture
def sample_agent() -> Agent:
    return Agent(
        name="Test Agent",
        description="A test agent",
        inputs=[
            AgentInput(name="content", type="string", required=True, description="Input text"),
        ],
        system_prompt="You are a test agent.",
        critical_rules="- Be concise",
        source_file="test-agent.md",
    )


class TestAgentRunner:
    def test_validates_missing_input(self, mock_config: Config, sample_agent: Agent):
        runner = AgentRunner(mock_config)
        with pytest.raises(ValueError, match="Missing required input"):
            runner.run(sample_agent, {})

    def test_validates_empty_input(self, mock_config: Config, sample_agent: Agent):
        runner = AgentRunner(mock_config)
        with pytest.raises(ValueError, match="Empty required input"):
            runner.run(sample_agent, {"content": ""})

    @patch("runtime.runner.create_completion")
    def test_run_success(self, mock_create: MagicMock, mock_config: Config, sample_agent: Agent):
        mock_create.return_value = CompletionResult(
            content="Here is the improved content.",
            input_tokens=100,
            output_tokens=50,
        )

        runner = AgentRunner(mock_config)
        result = runner.run(sample_agent, {"content": "Fix this button label"})

        assert isinstance(result, AgentOutput)
        assert result.content == "Here is the improved content."
        assert result.agent_name == "Test Agent"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.latency_ms > 0

        # Verify the provider was called with correct parameters
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "test-model"
        assert call_kwargs["provider_name"] == "anthropic"
        assert "You are a test agent" in call_kwargs["system"]

    @patch("runtime.runner.create_completion")
    def test_run_with_model_override(self, mock_create: MagicMock, mock_config: Config, sample_agent: Agent):
        mock_create.return_value = CompletionResult(
            content="Result",
            input_tokens=10,
            output_tokens=5,
        )

        runner = AgentRunner(mock_config)
        result = runner.run(sample_agent, {"content": "test"}, model="claude-opus-4-6")

        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["model"] == "claude-opus-4-6"

    def test_system_message_composition(self, sample_agent: Agent):
        msg = sample_agent.build_system_message()
        assert "You are a test agent." in msg
        assert "Be concise" in msg

    def test_user_message_composition(self, sample_agent: Agent):
        msg = sample_agent.build_user_message({"content": "Fix my button"})
        assert "Fix my button" in msg

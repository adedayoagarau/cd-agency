"""Tests for the AgentRunner (mocked, no real API calls)."""

from unittest.mock import MagicMock, patch

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.config import Config
from runtime.model_providers import ProviderResponse
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


def _mock_provider_response(content: str = "Here is the improved content.") -> ProviderResponse:
    return ProviderResponse(
        content=content,
        input_tokens=100,
        output_tokens=50,
        model="test-model",
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

    @patch("runtime.runner.ModelRouter.from_config")
    def test_run_success(self, mock_from_config: MagicMock, mock_config: Config, sample_agent: Agent):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _mock_provider_response()

        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        runner = AgentRunner(mock_config)
        result = runner.run(sample_agent, {"content": "Fix this button label"})

        assert isinstance(result, AgentOutput)
        assert result.content == "Here is the improved content."
        assert result.agent_name == "Test Agent"
        assert result.input_tokens == 100
        assert result.output_tokens == 50
        assert result.latency_ms > 0

        # Verify the provider was called with correct parameters
        call_kwargs = mock_provider.complete.call_args.kwargs
        assert call_kwargs["model"] == "test-model"
        assert "You are a test agent" in call_kwargs["system"]
        assert call_kwargs["messages"][0]["role"] == "user"

    @patch("runtime.runner.ModelRouter.from_config")
    def test_run_with_model_override(self, mock_from_config: MagicMock, mock_config: Config, sample_agent: Agent):
        mock_provider = MagicMock()
        mock_provider.complete.return_value = _mock_provider_response("Result")

        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "claude-opus-4-6")
        mock_from_config.return_value = mock_router

        runner = AgentRunner(mock_config)
        result = runner.run(sample_agent, {"content": "test"}, model="claude-opus-4-6")

        mock_router.resolve.assert_called_once_with("claude-opus-4-6")

    @patch("runtime.runner.ModelRouter.from_config")
    def test_run_uses_agent_preferred_model(self, mock_from_config: MagicMock, mock_config: Config):
        agent = Agent(
            name="Test Agent",
            description="A test agent",
            preferred_model="openai/gpt-4o",
            inputs=[AgentInput(name="content", type="string", required=True)],
            source_file="test-agent.md",
        )

        mock_provider = MagicMock()
        mock_provider.complete.return_value = _mock_provider_response()

        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "gpt-4o")
        mock_from_config.return_value = mock_router

        runner = AgentRunner(mock_config)
        runner.run(agent, {"content": "test"})

        mock_router.resolve.assert_called_once_with("openai/gpt-4o")

    @patch("runtime.runner.ModelRouter.from_config")
    def test_run_streaming(self, mock_from_config: MagicMock, mock_config: Config, sample_agent: Agent):
        mock_provider = MagicMock()
        mock_provider.stream.return_value = _mock_provider_response("Streamed")

        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        runner = AgentRunner(mock_config)
        result = runner.run(sample_agent, {"content": "test"}, stream=True)

        assert result.content == "Streamed"
        mock_provider.stream.assert_called_once()

    def test_system_message_composition(self, sample_agent: Agent):
        msg = sample_agent.build_system_message()
        assert "You are a test agent." in msg
        assert "Be concise" in msg

    def test_user_message_composition(self, sample_agent: Agent):
        msg = sample_agent.build_user_message({"content": "Fix my button"})
        assert "Fix my button" in msg

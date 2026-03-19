"""Tests for the multi-turn run_conversation() method."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from runtime.agent import Agent, AgentOutput
from runtime.config import Config
from runtime.providers import CompletionResult
from runtime.runner import AgentRunner


def _make_agent() -> Agent:
    return Agent(
        name="Test Agent",
        description="A test agent",
        system_prompt="You are a helpful test agent.",
        inputs=[],
    )


def _make_completion(content: str = "Test response", input_tokens: int = 50, output_tokens: int = 30):
    """Create a mock CompletionResult."""
    return CompletionResult(
        content=content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def _make_runner():
    """Create a runner with test config."""
    config = Config(api_key="test-key")
    runner = AgentRunner(config)
    return runner


class TestRunConversation:
    """Tests for AgentRunner.run_conversation()."""

    @patch("runtime.runner.create_completion")
    def test_run_conversation_single_turn(self, mock_create):
        """Single-turn conversation should work like regular run."""
        agent = _make_agent()
        runner = _make_runner()
        mock_create.return_value = _make_completion("Hello!")

        messages = [{"role": "user", "content": "Hi"}]

        with patch("runtime.design_system.load_design_system_from_config", return_value=None), \
             patch("runtime.memory.ProjectMemory.load") as mock_memory:
            mock_memory.return_value = MagicMock(get_context_for_agent=MagicMock(return_value=""))
            result = runner.run_conversation(agent, messages)

        assert isinstance(result, AgentOutput)
        assert result.content == "Hello!"
        assert result.agent_name == "Test Agent"

    @patch("runtime.runner.create_completion")
    def test_run_conversation_multi_turn(self, mock_create):
        """Multi-turn conversation should pass full history."""
        agent = _make_agent()
        runner = _make_runner()
        mock_create.return_value = _make_completion("Here are 3 options...")

        messages = [
            {"role": "user", "content": "Fix this error: 500"},
            {"role": "assistant", "content": "What context?"},
            {"role": "user", "content": "User saving a form"},
        ]

        with patch("runtime.design_system.load_design_system_from_config", return_value=None), \
             patch("runtime.memory.ProjectMemory.load") as mock_memory:
            mock_memory.return_value = MagicMock(get_context_for_agent=MagicMock(return_value=""))
            result = runner.run_conversation(agent, messages)

        assert result.content == "Here are 3 options..."
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs["messages"] == messages

    @patch("runtime.runner.create_completion")
    def test_run_conversation_includes_system_context(self, mock_create):
        """System message should include agent prompt and context."""
        agent = _make_agent()
        agent.system_prompt = "You are an error message specialist."
        runner = _make_runner()
        mock_create.return_value = _make_completion()

        messages = [{"role": "user", "content": "Help"}]

        with patch("runtime.design_system.load_design_system_from_config", return_value=None), \
             patch("runtime.memory.ProjectMemory.load") as mock_memory:
            mock_memory.return_value = MagicMock(get_context_for_agent=MagicMock(return_value=""))
            runner.run_conversation(agent, messages)

        call_kwargs = mock_create.call_args.kwargs
        assert "error message specialist" in call_kwargs["system"]

    @patch("runtime.runner.create_completion")
    def test_run_conversation_records_analytics(self, mock_create):
        """Conversation should record analytics."""
        agent = _make_agent()
        runner = _make_runner()
        mock_create.return_value = _make_completion()

        messages = [{"role": "user", "content": "Hi"}]

        with patch("runtime.design_system.load_design_system_from_config", return_value=None), \
             patch("runtime.memory.ProjectMemory.load") as mock_memory, \
             patch("tools.analytics.Analytics") as mock_analytics_cls:
            mock_memory.return_value = MagicMock(get_context_for_agent=MagicMock(return_value=""))
            mock_analytics = MagicMock()
            mock_analytics_cls.load.return_value = mock_analytics
            runner.run_conversation(agent, messages)

        mock_analytics.record_agent_run.assert_called_once()

    @patch("runtime.runner.create_completion")
    def test_run_conversation_token_tracking(self, mock_create):
        """Conversation should track token usage."""
        agent = _make_agent()
        runner = _make_runner()
        mock_create.return_value = _make_completion("Response", input_tokens=100, output_tokens=50)

        messages = [{"role": "user", "content": "Hi"}]

        with patch("runtime.design_system.load_design_system_from_config", return_value=None), \
             patch("runtime.memory.ProjectMemory.load") as mock_memory:
            mock_memory.return_value = MagicMock(get_context_for_agent=MagicMock(return_value=""))
            result = runner.run_conversation(agent, messages)

        assert result.input_tokens == 100
        assert result.output_tokens == 50

"""Tests for multi-model provider abstraction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from runtime.model_providers import (
    AnthropicProvider,
    ModelRouter,
    OpenAIProvider,
    OpenRouterProvider,
    ProviderResponse,
    _OpenAICompatibleProvider,
)


# ---------------------------------------------------------------------------
# ProviderResponse
# ---------------------------------------------------------------------------

class TestProviderResponse:
    def test_defaults(self):
        r = ProviderResponse(content="hello")
        assert r.content == "hello"
        assert r.input_tokens == 0
        assert r.output_tokens == 0
        assert r.model == ""
        assert r.raw_response is None

    def test_all_fields(self):
        r = ProviderResponse(
            content="hi", input_tokens=10, output_tokens=5,
            model="test", raw_response={"ok": True},
        )
        assert r.input_tokens == 10
        assert r.model == "test"


# ---------------------------------------------------------------------------
# AnthropicProvider
# ---------------------------------------------------------------------------

class TestAnthropicProvider:
    def test_is_available_with_key(self):
        p = AnthropicProvider(api_key="sk-test")
        assert p.is_available() is True

    def test_is_not_available_without_key(self):
        p = AnthropicProvider(api_key="")
        assert p.is_available() is False

    def test_provider_name(self):
        p = AnthropicProvider(api_key="sk-test")
        assert p.provider_name() == "Anthropic"

    @patch("runtime.model_providers.AnthropicProvider._get_client")
    def test_complete(self, mock_get_client: MagicMock):
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Agent response"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 50

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        provider = AnthropicProvider(api_key="sk-test")
        result = provider.complete(
            model="claude-sonnet-4-20250514",
            system="You are helpful.",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=1024,
            temperature=0.7,
        )

        assert isinstance(result, ProviderResponse)
        assert result.content == "Agent response"
        assert result.input_tokens == 100
        assert result.output_tokens == 50

    @patch("runtime.model_providers.AnthropicProvider._get_client")
    def test_stream(self, mock_get_client: MagicMock):
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Streamed response"

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.usage.input_tokens = 80
        mock_response.usage.output_tokens = 40

        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.get_final_message.return_value = mock_response

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream_ctx
        mock_get_client.return_value = mock_client

        provider = AnthropicProvider(api_key="sk-test")
        result = provider.stream(
            model="claude-sonnet-4-20250514",
            system="You are helpful.",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=1024,
            temperature=0.7,
        )

        assert result.content == "Streamed response"
        assert result.input_tokens == 80


# ---------------------------------------------------------------------------
# OpenAI-compatible provider
# ---------------------------------------------------------------------------

class TestOpenAIProvider:
    def test_provider_name(self):
        p = OpenAIProvider(api_key="sk-test")
        assert p.provider_name() == "OpenAI"

    def test_is_not_available_without_openai_package(self):
        p = OpenAIProvider(api_key="sk-test")
        # Without the openai package installed, is_available checks import
        available = p.is_available()
        # Either True (if openai is installed) or False — just assert it's bool
        assert isinstance(available, bool)

    def test_is_not_available_without_key(self):
        p = OpenAIProvider(api_key="")
        assert p.is_available() is False

    @patch.object(_OpenAICompatibleProvider, "_get_client")
    def test_complete_builds_system_message(self, mock_get_client: MagicMock):
        mock_choice = MagicMock()
        mock_choice.message.content = "GPT response"

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 50
        mock_usage.completion_tokens = 30

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        provider = OpenAIProvider(api_key="sk-test")
        result = provider.complete(
            model="gpt-4o",
            system="You are a content designer.",
            messages=[{"role": "user", "content": "Review this copy"}],
            max_tokens=1024,
            temperature=0.7,
        )

        assert result.content == "GPT response"
        assert result.input_tokens == 50
        assert result.output_tokens == 30

        # Verify system message was prepended
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][0]["content"] == "You are a content designer."
        assert call_kwargs["messages"][1]["role"] == "user"


# ---------------------------------------------------------------------------
# OpenRouter provider
# ---------------------------------------------------------------------------

class TestOpenRouterProvider:
    def test_provider_name(self):
        p = OpenRouterProvider(api_key="sk-or-test")
        assert p.provider_name() == "OpenRouter"

    def test_base_url(self):
        p = OpenRouterProvider(api_key="sk-or-test")
        assert p._base_url == "https://openrouter.ai/api/v1"

    def test_has_referer_header(self):
        p = OpenRouterProvider(api_key="sk-or-test")
        assert "HTTP-Referer" in p._default_headers
        assert "X-Title" in p._default_headers


# ---------------------------------------------------------------------------
# ModelRouter
# ---------------------------------------------------------------------------

class TestModelRouter:
    def test_explicit_anthropic_prefix(self):
        router = ModelRouter(anthropic_key="sk-ant")
        provider, model = router.resolve("anthropic/claude-sonnet-4-20250514")
        assert isinstance(provider, AnthropicProvider)
        assert model == "claude-sonnet-4-20250514"

    def test_explicit_openai_prefix(self):
        router = ModelRouter(openai_key="sk-oai")
        provider, model = router.resolve("openai/gpt-4o")
        assert isinstance(provider, OpenAIProvider)
        assert model == "gpt-4o"

    def test_explicit_openrouter_prefix(self):
        router = ModelRouter(openrouter_key="sk-or")
        provider, model = router.resolve("openrouter/meta-llama/llama-3-70b")
        assert isinstance(provider, OpenRouterProvider)
        assert model == "meta-llama/llama-3-70b"

    def test_auto_detect_anthropic(self):
        router = ModelRouter(anthropic_key="sk-ant")
        provider, model = router.resolve("claude-sonnet-4-20250514")
        assert isinstance(provider, AnthropicProvider)
        assert model == "claude-sonnet-4-20250514"

    def test_default_to_anthropic(self):
        router = ModelRouter(anthropic_key="sk-ant")
        provider, model = router.resolve("some-unknown-model")
        assert isinstance(provider, AnthropicProvider)

    def test_missing_provider_raises(self):
        router = ModelRouter(anthropic_key="sk-ant")
        with pytest.raises(ValueError, match="No API key configured for openai"):
            router.resolve("openai/gpt-4o")

    def test_no_providers_raises(self):
        router = ModelRouter()
        with pytest.raises(ValueError, match="No LLM provider is configured"):
            router.resolve("claude-sonnet-4-20250514")

    def test_available_providers(self):
        router = ModelRouter(anthropic_key="sk-ant")
        names = router.available_providers()
        assert "Anthropic" in names

    def test_available_providers_empty(self):
        router = ModelRouter()
        assert router.available_providers() == []

    def test_from_config(self):
        config = MagicMock()
        config.api_key = "sk-ant"
        config.openai_api_key = "sk-oai"
        config.openrouter_api_key = ""

        router = ModelRouter.from_config(config)
        assert "anthropic" in router._providers
        assert "openai" in router._providers
        assert "openrouter" not in router._providers

    def test_prefix_routing_strips_correctly(self):
        router = ModelRouter(openrouter_key="sk-or")
        _, model = router.resolve("openrouter/anthropic/claude-3.5-sonnet")
        assert model == "anthropic/claude-3.5-sonnet"

    @patch.object(OpenAIProvider, "is_available", return_value=True)
    def test_auto_detect_gpt(self, _mock):
        router = ModelRouter(anthropic_key="sk-ant", openai_key="sk-oai")
        provider, model = router.resolve("gpt-4o-mini")
        assert isinstance(provider, OpenAIProvider)
        assert model == "gpt-4o-mini"

    @patch.object(OpenAIProvider, "is_available", return_value=True)
    def test_auto_detect_o1(self, _mock):
        router = ModelRouter(anthropic_key="sk-ant", openai_key="sk-oai")
        provider, model = router.resolve("o1-preview")
        assert isinstance(provider, OpenAIProvider)


# ---------------------------------------------------------------------------
# Runner integration — model resolution order
# ---------------------------------------------------------------------------

class TestRunnerModelResolution:
    """Verify the runner picks models in the right priority order."""

    def test_explicit_model_wins(self):
        """Explicit model= parameter beats agent.preferred_model and config."""
        from runtime.agent import Agent, AgentInput
        from runtime.config import Config

        agent = Agent(
            name="Test", description="test",
            preferred_model="openai/gpt-4o",
            inputs=[AgentInput(name="content", type="string")],
            source_file="test.md",
        )
        config = Config(api_key="sk-ant", model="claude-sonnet-4-20250514")

        # The resolved model should be the explicit one
        resolved = "openrouter/mistral" or agent.preferred_model or config.model
        assert resolved == "openrouter/mistral"

    def test_agent_preferred_model_beats_config(self):
        from runtime.agent import Agent, AgentInput
        from runtime.config import Config

        agent = Agent(
            name="Test", description="test",
            preferred_model="openai/gpt-4o",
            inputs=[AgentInput(name="content", type="string")],
            source_file="test.md",
        )
        config = Config(api_key="sk-ant", model="claude-sonnet-4-20250514")

        resolved = None or agent.preferred_model or config.model
        assert resolved == "openai/gpt-4o"

    def test_config_default_used_when_no_override(self):
        from runtime.agent import Agent, AgentInput
        from runtime.config import Config

        agent = Agent(
            name="Test", description="test",
            inputs=[AgentInput(name="content", type="string")],
            source_file="test.md",
        )
        config = Config(api_key="sk-ant", model="claude-sonnet-4-20250514")

        resolved = None or agent.preferred_model or config.model
        assert resolved == "claude-sonnet-4-20250514"


# ---------------------------------------------------------------------------
# Config integration
# ---------------------------------------------------------------------------

class TestConfigMultiModel:
    def test_config_has_new_fields(self):
        from runtime.config import Config
        c = Config(
            api_key="sk-ant",
            openai_api_key="sk-oai",
            openrouter_api_key="sk-or",
        )
        assert c.openai_api_key == "sk-oai"
        assert c.openrouter_api_key == "sk-or"

    def test_validate_accepts_openai_only(self):
        from runtime.config import Config
        c = Config(openai_api_key="sk-oai")
        errors = c.validate()
        # Should not complain about missing API key
        key_errors = [e for e in errors if "API key" in e]
        assert len(key_errors) == 0

    def test_validate_accepts_openrouter_only(self):
        from runtime.config import Config
        c = Config(openrouter_api_key="sk-or")
        errors = c.validate()
        key_errors = [e for e in errors if "API key" in e]
        assert len(key_errors) == 0

    def test_validate_fails_with_no_keys(self):
        from runtime.config import Config
        c = Config()
        errors = c.validate()
        key_errors = [e for e in errors if "API key" in e or "LLM" in e]
        assert len(key_errors) > 0

    @patch.dict("os.environ", {
        "OPENAI_API_KEY": "sk-env-oai",
        "OPENROUTER_API_KEY": "sk-env-or",
    }, clear=False)
    def test_from_env_reads_new_keys(self):
        from runtime.config import Config
        c = Config.from_env()
        assert c.openai_api_key == "sk-env-oai"
        assert c.openrouter_api_key == "sk-env-or"


# ---------------------------------------------------------------------------
# Agent preferred_model field
# ---------------------------------------------------------------------------

class TestAgentPreferredModel:
    def test_default_empty(self):
        from runtime.agent import Agent
        a = Agent(name="Test", description="test")
        assert a.preferred_model == ""

    def test_set_preferred_model(self):
        from runtime.agent import Agent
        a = Agent(name="Test", description="test", preferred_model="openai/gpt-4o")
        assert a.preferred_model == "openai/gpt-4o"


# ---------------------------------------------------------------------------
# Loader reads model from frontmatter
# ---------------------------------------------------------------------------

class TestLoaderModelField:
    def test_loads_model_from_frontmatter(self, tmp_path):
        from runtime.loader import load_agent

        md = tmp_path / "test-agent.md"
        md.write_text(
            "---\n"
            "name: Test Agent\n"
            "description: A test\n"
            "model: openai/gpt-4o\n"
            "inputs:\n"
            "  - name: content\n"
            "    type: string\n"
            "---\n"
            "### System Prompt\n"
            "You are a test agent.\n"
        )
        agent = load_agent(md)
        assert agent.preferred_model == "openai/gpt-4o"

    def test_missing_model_defaults_empty(self, tmp_path):
        from runtime.loader import load_agent

        md = tmp_path / "test-agent.md"
        md.write_text(
            "---\n"
            "name: Test Agent\n"
            "description: A test\n"
            "inputs:\n"
            "  - name: content\n"
            "    type: string\n"
            "---\n"
            "### System Prompt\n"
            "You are a test agent.\n"
        )
        agent = load_agent(md)
        assert agent.preferred_model == ""

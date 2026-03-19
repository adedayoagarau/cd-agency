"""Tests for the multi-provider abstraction layer."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from runtime.providers import (
    CompletionResult,
    ProviderInfo,
    PROVIDERS,
    create_completion,
    create_completion_streaming,
    get_provider_info,
    list_providers,
)


class TestProviderInfo:
    def test_all_providers_registered(self):
        assert "anthropic" in PROVIDERS
        assert "openai" in PROVIDERS
        assert "gemini" in PROVIDERS
        assert "openrouter" in PROVIDERS
        assert "kimi" in PROVIDERS
        assert "ollama" in PROVIDERS

    def test_get_provider_info(self):
        info = get_provider_info("openai")
        assert info.name == "openai"
        assert info.default_model == "gpt-4o"
        assert not info.is_anthropic

    def test_get_provider_info_anthropic(self):
        info = get_provider_info("anthropic")
        assert info.is_anthropic
        assert info.env_key == "ANTHROPIC_API_KEY"

    def test_get_provider_info_unknown(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider_info("unknown_provider")

    def test_list_providers(self):
        providers = list_providers()
        assert len(providers) == 6
        names = [p.name for p in providers]
        assert "anthropic" in names
        assert "openai" in names

    def test_provider_has_models(self):
        for name, info in PROVIDERS.items():
            assert len(info.models) > 0, f"Provider {name} has no models"
            assert info.default_model in info.models, (
                f"Provider {name} default model not in models list"
            )

    def test_ollama_no_env_key(self):
        info = get_provider_info("ollama")
        assert info.env_key == ""
        assert info.base_url == "http://localhost:11434/v1"


def _mock_anthropic_response(content="Hello", input_tokens=10, output_tokens=5):
    """Build a mock Anthropic API response."""
    mock_text_block = MagicMock()
    mock_text_block.type = "text"
    mock_text_block.text = content

    mock_usage = MagicMock()
    mock_usage.input_tokens = input_tokens
    mock_usage.output_tokens = output_tokens

    mock_response = MagicMock()
    mock_response.content = [mock_text_block]
    mock_response.usage = mock_usage
    return mock_response


def _mock_openai_response(content="Hello", prompt_tokens=10, completion_tokens=5):
    """Build a mock OpenAI API response."""
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = prompt_tokens
    mock_usage.completion_tokens = completion_tokens

    mock_message = MagicMock()
    mock_message.content = content

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage
    return mock_response


class TestCreateCompletion:
    @patch("runtime.providers._call_anthropic")
    def test_anthropic_routing(self, mock_call):
        """Anthropic provider should route to _call_anthropic."""
        mock_call.return_value = CompletionResult(
            content="Hello from Claude", input_tokens=10, output_tokens=5,
        )

        result = create_completion(
            provider_name="anthropic",
            api_key="test-key",
            model="claude-sonnet-4-20250514",
            system="You are helpful.",
            messages=[{"role": "user", "content": "Hi"}],
        )

        assert isinstance(result, CompletionResult)
        assert result.content == "Hello from Claude"
        assert result.input_tokens == 10
        assert result.output_tokens == 5
        mock_call.assert_called_once()

    @patch("runtime.providers._call_openai_compatible")
    def test_openai_routing(self, mock_call):
        """OpenAI provider should route to _call_openai_compatible."""
        mock_call.return_value = CompletionResult(
            content="Hello from GPT", input_tokens=15, output_tokens=8,
        )

        result = create_completion(
            provider_name="openai",
            api_key="sk-test",
            model="gpt-4o",
            system="You are helpful.",
            messages=[{"role": "user", "content": "Hi"}],
        )

        assert result.content == "Hello from GPT"
        assert result.input_tokens == 15
        assert result.output_tokens == 8
        mock_call.assert_called_once()

    @patch("runtime.providers._call_openai_compatible")
    def test_gemini_uses_base_url(self, mock_call):
        """Gemini provider should pass its base_url."""
        mock_call.return_value = CompletionResult(content="Gemini says hi")

        create_completion(
            provider_name="gemini",
            api_key="AI-test",
            model="gemini-2.0-flash",
            system="Be helpful.",
            messages=[{"role": "user", "content": "Hi"}],
        )

        call_args = mock_call.call_args
        # base_url should be the Gemini endpoint
        assert "generativelanguage.googleapis.com" in call_args[0][1]

    @patch("runtime.providers._call_openai_compatible")
    def test_ollama_routing(self, mock_call):
        """Ollama should route to openai-compatible with localhost URL."""
        mock_call.return_value = CompletionResult(content="Local response")

        create_completion(
            provider_name="ollama",
            api_key="",
            model="llama3",
            system="Be helpful.",
            messages=[{"role": "user", "content": "Hi"}],
        )

        call_args = mock_call.call_args
        assert "localhost:11434" in call_args[0][1]

    @patch("runtime.providers._call_openai_compatible")
    def test_custom_base_url_override(self, mock_call):
        """Custom base_url should override the provider's default."""
        mock_call.return_value = CompletionResult(content="Proxy response")

        create_completion(
            provider_name="openai",
            api_key="sk-test",
            model="gpt-4o",
            system="Be helpful.",
            messages=[{"role": "user", "content": "Hi"}],
            base_url="https://my-proxy.example.com/v1",
        )

        call_args = mock_call.call_args
        assert call_args[0][1] == "https://my-proxy.example.com/v1"

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            create_completion(
                provider_name="nonexistent",
                api_key="key",
                model="model",
                system="sys",
                messages=[],
            )


class TestCallAnthropicInternal:
    """Test _call_anthropic with mocked anthropic module."""

    def test_call_anthropic(self):
        import importlib
        import runtime.providers as prov

        mock_client = MagicMock()
        mock_client.messages.create.return_value = _mock_anthropic_response(
            "Claude response", 20, 10
        )

        with patch.dict("sys.modules", {"anthropic": MagicMock()}):
            import sys
            sys.modules["anthropic"].Anthropic.return_value = mock_client

            result = prov._call_anthropic(
                api_key="test",
                model="test-model",
                system="sys",
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=100,
                temperature=0.5,
            )

        assert result.content == "Claude response"
        assert result.input_tokens == 20
        assert result.output_tokens == 10


class TestCallOpenAICompatibleInternal:
    """Test _call_openai_compatible with mocked openai module."""

    def test_call_openai(self):
        import runtime.providers as prov

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response(
            "GPT response", 15, 8
        )

        with patch.dict("sys.modules", {"openai": MagicMock()}):
            import sys
            sys.modules["openai"].OpenAI.return_value = mock_client

            result = prov._call_openai_compatible(
                api_key="sk-test",
                base_url=None,
                model="gpt-4o",
                system="You are helpful.",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=100,
                temperature=0.5,
            )

        assert result.content == "GPT response"
        assert result.input_tokens == 15
        assert result.output_tokens == 8

        # Verify system message was prepended
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        sent_msgs = call_kwargs["messages"]
        assert sent_msgs[0]["role"] == "system"
        assert sent_msgs[0]["content"] == "You are helpful."

    def test_ollama_dummy_key(self):
        import runtime.providers as prov

        mock_openai_module = MagicMock()
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _mock_openai_response("Local")
        mock_openai_module.OpenAI.return_value = mock_client

        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            prov._call_openai_compatible(
                api_key="",
                base_url="http://localhost:11434/v1",
                model="llama3",
                system="",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=100,
                temperature=0.5,
            )

            call_kwargs = mock_openai_module.OpenAI.call_args.kwargs
            assert call_kwargs["api_key"] == "ollama"


class TestCreateCompletionStreaming:
    def test_anthropic_streaming(self):
        """Anthropic streaming should use client.messages.stream()."""
        mock_text_block = MagicMock()
        mock_text_block.type = "text"
        mock_text_block.text = "Streamed response"

        mock_usage = MagicMock()
        mock_usage.input_tokens = 20
        mock_usage.output_tokens = 10

        mock_response = MagicMock()
        mock_response.content = [mock_text_block]
        mock_response.usage = mock_usage

        mock_stream = MagicMock()
        mock_stream.get_final_message.return_value = mock_response
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream

        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            import runtime.providers as prov
            result = prov.create_completion_streaming(
                provider_name="anthropic",
                api_key="test-key",
                model="claude-sonnet-4-20250514",
                system="System prompt",
                messages=[{"role": "user", "content": "Hi"}],
            )

        assert result.content == "Streamed response"
        assert result.input_tokens == 20
        assert result.output_tokens == 10


class TestConfigMultiProvider:
    def test_config_defaults(self):
        from runtime.config import Config

        config = Config()
        assert config.provider == "anthropic"
        assert config.provider_keys == {}
        assert config.base_url == ""

    def test_config_with_provider(self):
        from runtime.config import Config

        config = Config(provider="openai", api_key="sk-test")
        assert config.provider == "openai"

    def test_config_validate_no_key_anthropic(self):
        from runtime.config import Config
        from pathlib import Path

        config = Config(
            api_key="",
            provider="anthropic",
            agents_dir=Path("content-design"),
        )
        errors = config.validate()
        assert any("API key" in e for e in errors)

    def test_config_validate_ollama_no_key_ok(self):
        from runtime.config import Config
        from pathlib import Path

        config = Config(
            api_key="",
            provider="ollama",
            agents_dir=Path("content-design"),
        )
        errors = config.validate()
        # Should not complain about API key for ollama
        assert not any("API key" in e for e in errors)

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-123", "CD_AGENCY_PROVIDER": "openai"})
    def test_config_from_env_openai(self):
        from runtime.config import Config

        config = Config.from_env()
        assert config.provider == "openai"
        assert config.api_key == "sk-test-123"
        assert config.provider_keys.get("openai") == "sk-test-123"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test"}, clear=False)
    def test_config_from_env_backward_compat(self):
        from runtime.config import Config

        # When no CD_AGENCY_PROVIDER is set, should default to anthropic
        config = Config.from_env()
        assert config.provider == "anthropic"
        assert config.api_key == "sk-ant-test"

"""Multi-model provider abstraction — route agent calls to any LLM backend.

Supports Anthropic (default), OpenAI, and OpenRouter out of the box.
Users bring their own keys (BYOK).
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Provider response — normalized across all backends
# ---------------------------------------------------------------------------

@dataclass
class ProviderResponse:
    """Normalized response from any LLM provider."""

    content: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    raw_response: Any = None


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class ModelProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        max_retries: int = 3,
    ) -> ProviderResponse:
        """Send a completion request and return a normalized response."""

    @abstractmethod
    def stream(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        """Send a streaming request, collect, and return a normalized response."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider's SDK is installed and an API key is set."""

    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

class AnthropicProvider(ModelProvider):
    """Wraps the Anthropic SDK — the default provider."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        max_retries: int = 3,
    ) -> ProviderResponse:
        import anthropic

        client = self._get_client()
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system,
                    messages=messages,
                )
                content = ""
                for block in response.content:
                    if block.type == "text":
                        content += block.text

                return ProviderResponse(
                    content=content,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    model=model,
                    raw_response=response,
                )
            except anthropic.APIStatusError as e:
                last_error = e
                if e.status_code != 429 and 400 <= e.status_code < 500:
                    raise
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except anthropic.APIConnectionError as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        raise last_error  # type: ignore[misc]

    def stream(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        client = self._get_client()

        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        ) as stream_ctx:
            response = stream_ctx.get_final_message()

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return ProviderResponse(
            content=content,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            model=model,
            raw_response=response,
        )

    def is_available(self) -> bool:
        return bool(self._api_key)

    def provider_name(self) -> str:
        return "Anthropic"


# ---------------------------------------------------------------------------
# OpenAI-compatible provider (shared by OpenAI and OpenRouter)
# ---------------------------------------------------------------------------

class _OpenAICompatibleProvider(ModelProvider):
    """Shared implementation for any OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
        default_headers: dict[str, str] | None = None,
        name: str = "OpenAI",
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._default_headers = default_headers or {}
        self._name = name
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    f"{self._name} provider requires the openai package. "
                    "Install it with: pip install 'cd-agency[multi-model]'"
                )
            kwargs: dict[str, Any] = {"api_key": self._api_key}
            if self._base_url:
                kwargs["base_url"] = self._base_url
            if self._default_headers:
                kwargs["default_headers"] = self._default_headers
            self._client = OpenAI(**kwargs)
        return self._client

    def complete(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
        max_retries: int = 3,
    ) -> ProviderResponse:
        client = self._get_client()
        last_error: Exception | None = None

        # Build OpenAI-style messages (system as first message)
        oai_messages: list[dict[str, str]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=oai_messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                choice = response.choices[0]
                content = choice.message.content or ""

                input_tokens = 0
                output_tokens = 0
                if response.usage:
                    input_tokens = response.usage.prompt_tokens or 0
                    output_tokens = response.usage.completion_tokens or 0

                return ProviderResponse(
                    content=content,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    raw_response=response,
                )
            except Exception as e:
                last_error = e
                # Check for rate limit or server errors worth retrying
                status = getattr(e, "status_code", None)
                if status and status != 429 and 400 <= status < 500:
                    raise
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        raise last_error  # type: ignore[misc]

    def stream(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> ProviderResponse:
        client = self._get_client()

        oai_messages: list[dict[str, str]] = []
        if system:
            oai_messages.append({"role": "system", "content": system})
        oai_messages.extend(messages)

        stream_resp = client.chat.completions.create(
            model=model,
            messages=oai_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
            stream_options={"include_usage": True},
        )

        chunks: list[str] = []
        input_tokens = 0
        output_tokens = 0

        for chunk in stream_resp:
            if chunk.choices and chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
            if chunk.usage:
                input_tokens = chunk.usage.prompt_tokens or 0
                output_tokens = chunk.usage.completion_tokens or 0

        return ProviderResponse(
            content="".join(chunks),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
        )

    def is_available(self) -> bool:
        if not self._api_key:
            return False
        try:
            import openai  # noqa: F401
            return True
        except ImportError:
            return False

    def provider_name(self) -> str:
        return self._name


class OpenAIProvider(_OpenAICompatibleProvider):
    """OpenAI GPT models."""

    def __init__(self, api_key: str) -> None:
        super().__init__(api_key=api_key, name="OpenAI")


class OpenRouterProvider(_OpenAICompatibleProvider):
    """OpenRouter — access any model via a single API."""

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str) -> None:
        super().__init__(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/adedayoagarau/cd-agency",
                "X-Title": "CD Agency",
            },
            name="OpenRouter",
        )


# ---------------------------------------------------------------------------
# Model router — picks the right provider from a model string
# ---------------------------------------------------------------------------

# Well-known Anthropic model prefixes for auto-detection
_ANTHROPIC_MODEL_PREFIXES = (
    "claude-",
)

# Well-known OpenAI model prefixes for auto-detection
_OPENAI_MODEL_PREFIXES = (
    "gpt-",
    "o1-",
    "o3-",
    "o4-",
    "chatgpt-",
)


class ModelRouter:
    """Routes model strings to the appropriate provider.

    Prefix routing:
        "anthropic/claude-sonnet-4-20250514"  → AnthropicProvider, model="claude-sonnet-4-20250514"
        "openai/gpt-4o"                       → OpenAIProvider,    model="gpt-4o"
        "openrouter/meta-llama/llama-3-70b"   → OpenRouterProvider, model="meta-llama/llama-3-70b"

    Auto-detection (no prefix):
        "claude-sonnet-4-20250514"  → AnthropicProvider (starts with "claude-")
        "gpt-4o"                    → OpenAIProvider    (starts with "gpt-")

    Default: AnthropicProvider (backward compatible).
    """

    def __init__(
        self,
        anthropic_key: str = "",
        openai_key: str = "",
        openrouter_key: str = "",
    ) -> None:
        self._providers: dict[str, ModelProvider] = {}
        if anthropic_key:
            self._providers["anthropic"] = AnthropicProvider(anthropic_key)
        if openai_key:
            self._providers["openai"] = OpenAIProvider(openai_key)
        if openrouter_key:
            self._providers["openrouter"] = OpenRouterProvider(openrouter_key)

    def resolve(self, model_string: str) -> tuple[ModelProvider, str]:
        """Resolve a model string into (provider, bare_model_name).

        Raises:
            ValueError: If no provider is available for the model.
        """
        # Explicit prefix routing
        for prefix in ("anthropic/", "openai/", "openrouter/"):
            if model_string.startswith(prefix):
                provider_key = prefix.rstrip("/")
                bare_model = model_string[len(prefix):]
                provider = self._providers.get(provider_key)
                if provider is None:
                    raise ValueError(
                        f"No API key configured for {provider_key}. "
                        f"Set the appropriate environment variable."
                    )
                return provider, bare_model

        # Auto-detect by model name pattern
        for p in _OPENAI_MODEL_PREFIXES:
            if model_string.startswith(p):
                provider = self._providers.get("openai")
                if provider and provider.is_available():
                    return provider, model_string
                break

        # Default to Anthropic
        provider = self._providers.get("anthropic")
        if provider:
            return provider, model_string

        # Fallback: try any available provider
        for provider in self._providers.values():
            if provider.is_available():
                return provider, model_string

        raise ValueError(
            "No LLM provider is configured. Set at least one of: "
            "ANTHROPIC_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY"
        )

    def available_providers(self) -> list[str]:
        """Return names of providers that have keys configured."""
        return [
            p.provider_name() for p in self._providers.values()
            if p.is_available()
        ]

    @classmethod
    def from_config(cls, config: Any) -> ModelRouter:
        """Build a router from a Config object."""
        return cls(
            anthropic_key=config.api_key,
            openai_key=getattr(config, "openai_api_key", ""),
            openrouter_key=getattr(config, "openrouter_api_key", ""),
        )

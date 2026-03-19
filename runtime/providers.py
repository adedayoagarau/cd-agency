"""LLM provider abstraction — route to Anthropic, OpenAI, Gemini, OpenRouter, KIMI, or Ollama."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CompletionResult:
    """Normalized result from any LLM provider."""

    content: str
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class ProviderInfo:
    """Static metadata for a supported LLM provider."""

    name: str
    label: str
    base_url: str | None  # None = use SDK default
    default_model: str
    env_key: str  # environment variable name for API key
    models: list[str]
    key_placeholder: str = ""

    @property
    def is_anthropic(self) -> bool:
        return self.name == "anthropic"


PROVIDERS: dict[str, ProviderInfo] = {
    "anthropic": ProviderInfo(
        name="anthropic",
        label="Anthropic (Claude)",
        base_url=None,
        default_model="claude-sonnet-4-20250514",
        env_key="ANTHROPIC_API_KEY",
        models=[
            "claude-sonnet-4-20250514",
            "claude-opus-4-20250514",
            "claude-haiku-4-5-20251001",
        ],
        key_placeholder="sk-ant-...",
    ),
    "openai": ProviderInfo(
        name="openai",
        label="OpenAI",
        base_url=None,
        default_model="gpt-4o",
        env_key="OPENAI_API_KEY",
        models=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "o1", "o1-mini", "o3-mini"],
        key_placeholder="sk-...",
    ),
    "gemini": ProviderInfo(
        name="gemini",
        label="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        default_model="gemini-2.0-flash",
        env_key="GEMINI_API_KEY",
        models=["gemini-2.0-flash", "gemini-2.0-pro", "gemini-1.5-pro", "gemini-1.5-flash"],
        key_placeholder="AI...",
    ),
    "openrouter": ProviderInfo(
        name="openrouter",
        label="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        default_model="openrouter/auto",
        env_key="OPENROUTER_API_KEY",
        models=[
            "openrouter/auto",
            "anthropic/claude-sonnet-4-20250514",
            "openai/gpt-4o",
            "google/gemini-2.0-flash-001",
            "meta-llama/llama-3.1-405b-instruct",
            "mistralai/mixtral-8x7b-instruct",
        ],
        key_placeholder="sk-or-...",
    ),
    "kimi": ProviderInfo(
        name="kimi",
        label="KIMI (Moonshot)",
        base_url="https://api.moonshot.cn/v1",
        default_model="moonshot-v1-8k",
        env_key="KIMI_API_KEY",
        models=["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        key_placeholder="sk-...",
    ),
    "ollama": ProviderInfo(
        name="ollama",
        label="Ollama (Local)",
        base_url="http://localhost:11434/v1",
        default_model="llama3",
        env_key="",
        models=["llama3", "llama3.1", "mistral", "codellama", "phi3", "gemma2"],
        key_placeholder="(not required)",
    ),
}


def get_provider_info(name: str) -> ProviderInfo:
    """Get provider metadata by name. Raises ValueError if unknown."""
    if name not in PROVIDERS:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(PROVIDERS)}"
        )
    return PROVIDERS[name]


def list_providers() -> list[ProviderInfo]:
    """Return all supported providers."""
    return list(PROVIDERS.values())


def _call_anthropic(
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> CompletionResult:
    """Call Anthropic's native Messages API."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
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

    return CompletionResult(
        content=content,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
    )


def _call_openai_compatible(
    api_key: str,
    base_url: str | None,
    model: str,
    system: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> CompletionResult:
    """Call any OpenAI-compatible API (OpenAI, Gemini, OpenRouter, KIMI, Ollama)."""
    import openai

    kwargs: dict[str, Any] = {}
    if api_key:
        kwargs["api_key"] = api_key
    else:
        kwargs["api_key"] = "ollama"  # Ollama doesn't need a real key
    if base_url:
        kwargs["base_url"] = base_url

    client = openai.OpenAI(**kwargs)

    # Build messages with system as first message
    full_messages: list[dict[str, str]] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    response = client.chat.completions.create(
        model=model,
        messages=full_messages,  # type: ignore[arg-type]
        max_tokens=max_tokens,
        temperature=temperature,
    )

    content = response.choices[0].message.content or ""
    usage = response.usage
    input_tokens = usage.prompt_tokens if usage else 0
    output_tokens = usage.completion_tokens if usage else 0

    return CompletionResult(
        content=content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def create_completion(
    provider_name: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.7,
    base_url: str | None = None,
) -> CompletionResult:
    """Create a completion using the specified provider.

    Args:
        provider_name: Provider key (e.g. "anthropic", "openai", "gemini").
        api_key: API key for the provider.
        model: Model identifier to use.
        system: System prompt.
        messages: List of {"role": ..., "content": ...} message dicts.
        max_tokens: Maximum tokens to generate.
        temperature: Sampling temperature.
        base_url: Override the provider's default base URL.

    Returns:
        CompletionResult with content and token counts.
    """
    info = get_provider_info(provider_name)

    if info.is_anthropic:
        return _call_anthropic(api_key, model, system, messages, max_tokens, temperature)

    resolved_base_url = base_url or info.base_url
    return _call_openai_compatible(
        api_key, resolved_base_url, model, system, messages, max_tokens, temperature,
    )


def create_completion_streaming(
    provider_name: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict[str, str]],
    max_tokens: int = 4096,
    temperature: float = 0.7,
    base_url: str | None = None,
) -> CompletionResult:
    """Create a streaming completion, collecting the full response.

    For Anthropic, uses the native streaming API.
    For OpenAI-compatible providers, uses stream=True and collects chunks.
    """
    info = get_provider_info(provider_name)

    if info.is_anthropic:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return CompletionResult(
            content=content,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )

    # OpenAI-compatible streaming
    import openai

    kwargs: dict[str, Any] = {}
    kwargs["api_key"] = api_key or "ollama"
    resolved_base_url = base_url or info.base_url
    if resolved_base_url:
        kwargs["base_url"] = resolved_base_url

    client = openai.OpenAI(**kwargs)

    full_messages: list[dict[str, str]] = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    collected_content = ""
    input_tokens = 0
    output_tokens = 0

    stream_response = client.chat.completions.create(
        model=model,
        messages=full_messages,  # type: ignore[arg-type]
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )

    for chunk in stream_response:
        if chunk.choices and chunk.choices[0].delta.content:
            collected_content += chunk.choices[0].delta.content
        if chunk.usage:
            input_tokens = chunk.usage.prompt_tokens or 0
            output_tokens = chunk.usage.completion_tokens or 0

    return CompletionResult(
        content=collected_content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )

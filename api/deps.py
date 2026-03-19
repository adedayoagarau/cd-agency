"""FastAPI dependencies — registry, runner, and auth."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from runtime.config import Config
from runtime.registry import AgentRegistry
from runtime.runner import AgentRunner

# ── Paths ─────────────────────────────────────────────────────────────────────

CONTENT_DESIGN_DIR = Path(__file__).parent.parent / "content-design"
PRESETS_DIR = Path(__file__).parent.parent / "presets"

# ── Singletons ────────────────────────────────────────────────────────────────

_registry: AgentRegistry | None = None
_runner: AgentRunner | None = None


def get_registry() -> AgentRegistry:
    """Return a cached AgentRegistry loaded from the content-design/ directory."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry.from_directory(CONTENT_DESIGN_DIR)
    return _registry


def get_runner() -> AgentRunner:
    """Return a cached AgentRunner with configuration from the environment."""
    global _runner
    if _runner is None:
        config = Config.from_env()
        _runner = AgentRunner(config)
    return _runner


# ── Auth ──────────────────────────────────────────────────────────────────────


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
) -> str | None:
    """Optionally require an API key via the X-API-Key header.

    Enabled when the ``CD_AGENCY_REQUIRE_AUTH`` environment variable is set to
    a truthy value (``1``, ``true``, ``yes``).  When auth is required, the
    header value must match the ``CD_AGENCY_API_KEY`` environment variable.
    """
    require_auth = os.environ.get("CD_AGENCY_REQUIRE_AUTH", "").lower() in (
        "1",
        "true",
        "yes",
    )

    if not require_auth:
        return x_api_key

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )

    expected_key = os.environ.get("CD_AGENCY_API_KEY", "")
    if not expected_key or x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return x_api_key


# ── BYOK (Bring Your Own Key) ───────────────────────────────────────────────


async def get_runner_with_user_key(
    x_anthropic_key: Annotated[str | None, Header()] = None,
    x_llm_key: Annotated[str | None, Header()] = None,
    x_provider: Annotated[str | None, Header()] = None,
    x_model: Annotated[str | None, Header()] = None,
    x_base_url: Annotated[str | None, Header()] = None,
) -> AgentRunner:
    """Create an AgentRunner using the caller's LLM API key.

    Priority for provider:
    1. ``X-Provider`` header
    2. Server-side ``CD_AGENCY_PROVIDER`` env var
    3. Default: "anthropic"

    Priority for API key:
    1. ``X-LLM-Key`` header (multi-provider)
    2. ``X-Anthropic-Key`` header (backward compat)
    3. Server-side env var for the active provider
    4. 401 if no key available (except for ollama)
    """
    config = Config.from_env()

    # Resolve provider
    if x_provider:
        config.provider = x_provider

    # Resolve API key
    api_key = x_llm_key or x_anthropic_key or ""
    if not api_key:
        # Try provider-specific key from config
        api_key = config.provider_keys.get(config.provider, config.api_key)

    if not api_key and config.provider != "ollama":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API key required for provider '{config.provider}'. "
                   f"Provide via X-LLM-Key or X-Anthropic-Key header.",
        )

    config.api_key = api_key

    # Override model if specified
    if x_model:
        config.model = x_model

    # Override base URL if specified
    if x_base_url:
        config.base_url = x_base_url

    return AgentRunner(config)

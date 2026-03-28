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
    x_openai_key: Annotated[str | None, Header()] = None,
    x_openrouter_key: Annotated[str | None, Header()] = None,
) -> AgentRunner:
    """Create an AgentRunner using the caller's API keys.

    Priority:
    1. Request headers (user-provided, per-request)
    2. Server-side environment variables (fallback)
    3. 401 if no key is available

    Accepts ``X-Anthropic-Key``, ``X-OpenAI-Key``, and ``X-OpenRouter-Key``.
    """
    api_key = x_anthropic_key or os.environ.get("ANTHROPIC_API_KEY", "")
    openrouter_key = x_openrouter_key or os.environ.get("OPENROUTER_API_KEY", "")

    if not api_key and not openrouter_key and not x_openai_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Add your key in Settings > API Keys.",
        )

    config = Config.from_env()
    if api_key:
        config.api_key = api_key
    if x_openai_key:
        config.openai_api_key = x_openai_key
    if openrouter_key:
        config.openrouter_api_key = openrouter_key
        # If no Anthropic key, route through OpenRouter by default
        if not api_key:
            config.model = "openrouter/anthropic/claude-3.5-sonnet"
    return AgentRunner(config)

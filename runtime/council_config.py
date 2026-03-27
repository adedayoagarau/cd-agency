"""Council configuration — settings for multi-model consensus evaluation.

Council evaluation is an optional second-pass evaluator that uses multiple
LLM models to score content and produce a consensus quality score.
Disabled by default for backward compatibility.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = "config/quality_thresholds.yaml"

_VALID_CONSENSUS_METHODS = ("weighted_median", "mean", "median")

_VALID_TRIGGER_CONDITIONS = (
    "manual",
    "always",
    "high_stakes",
    "low_confidence",
    "quality_threshold_failed",
)

logger = logging.getLogger(__name__)


@dataclass
class CouncilConfig:
    """Configuration for multi-model council evaluation."""

    enabled: bool = False
    min_models: int = 2
    min_quorum: int = 2
    max_parallel: int = 3
    timeout_seconds: float = 30.0
    consensus_method: str = "weighted_median"
    confidence_threshold: float = 0.7
    trigger_conditions: list[str] = field(default_factory=lambda: ["manual"])
    enable_caching: bool = True
    cache_ttl_seconds: int = 300

    def __post_init__(self) -> None:
        if self.consensus_method not in _VALID_CONSENSUS_METHODS:
            raise ValueError(
                f"Invalid consensus method: {self.consensus_method!r}. "
                f"Must be one of {_VALID_CONSENSUS_METHODS}"
            )

    @classmethod
    def from_config(cls, config_path: str | Path | None = None) -> CouncilConfig:
        """Load council configuration from quality_thresholds.yaml."""
        if config_path is None:
            config_path = Path(_DEFAULT_CONFIG_PATH)
        else:
            config_path = Path(config_path)

        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)

            council_data = config_data.get("council", {}) if config_data else {}
            if not council_data:
                return cls()

            # Only pass known fields
            known = {f.name for f in cls.__dataclass_fields__.values()}
            filtered = {k: v for k, v in council_data.items() if k in known}
            return cls(**filtered)

        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning("Failed to load council config: %s. Using defaults.", e)
            return cls()

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Determine if council evaluation should be triggered."""
        if not self.enabled:
            return False

        if "always" in self.trigger_conditions:
            return True

        if "manual" in self.trigger_conditions and context.get("force_council", False):
            return True

        if "high_stakes" in self.trigger_conditions and context.get("high_stakes", False):
            return True

        if "low_confidence" in self.trigger_conditions:
            confidence = context.get("single_model_confidence", 1.0)
            if confidence < self.confidence_threshold:
                return True

        if "quality_threshold_failed" in self.trigger_conditions:
            if context.get("quality_threshold_failed", False):
                return True

        return False

    def get_available_models(self, model_router: Any) -> list[tuple[str, str]]:
        """Get list of (provider_key, model_name) pairs available for council.

        Returns at most ``max_parallel`` entries.
        """
        available: list[tuple[str, str]] = []

        # Map provider keys to default evaluation models
        provider_models = {
            "anthropic": "claude-sonnet-4-20250514",
            "openai": "gpt-4o-mini",
            "openrouter": "anthropic/claude-3-haiku",
        }

        for provider_key, default_model in provider_models.items():
            provider = model_router._providers.get(provider_key)
            if provider and provider.is_available():
                available.append((provider_key, default_model))

        return available[: self.max_parallel]

"""User-configurable quality thresholds — overrides evaluation profile defaults.

Reads from config/quality_thresholds.yaml if it exists, otherwise falls back
to the built-in evaluation profiles.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = "config/quality_thresholds.yaml"


class QualityConfig:
    """Loads and resolves quality thresholds from a YAML config file."""

    def __init__(self, config_path: str | Path = _DEFAULT_CONFIG_PATH) -> None:
        self.config_path = Path(config_path)
        self._config: dict[str, Any] | None = None

    @property
    def config(self) -> dict[str, Any]:
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
            except Exception:
                return {}
        return {}

    def get_threshold(self, agent_slug: str, metric: str) -> float:
        """Resolve a threshold: user config > evaluation profile > default.

        Args:
            agent_slug: Agent identifier (e.g. 'cta-optimization-specialist').
            metric: Threshold name (e.g. 'composite_score', 'readability_min').

        Returns:
            The threshold value.
        """
        # Check agent-specific user override
        user_val = self.config.get(agent_slug, {}).get(metric)
        if user_val is not None:
            return float(user_val)

        # Check global user override
        global_val = self.config.get("global", {}).get(metric)
        if global_val is not None:
            return float(global_val)

        # Fall back to evaluation profile
        from runtime.evaluation_profiles import get_evaluation_profile

        profile = get_evaluation_profile(agent_slug)
        return float(profile["thresholds"].get(metric, 70))

    def get_all_thresholds(self, agent_slug: str) -> dict[str, float]:
        """Return all resolved thresholds for an agent."""
        from runtime.evaluation_profiles import get_evaluation_profile

        profile = get_evaluation_profile(agent_slug)
        thresholds = dict(profile["thresholds"])

        # Override with global
        for k, v in self.config.get("global", {}).items():
            thresholds[k] = float(v)

        # Override with agent-specific
        for k, v in self.config.get(agent_slug, {}).items():
            thresholds[k] = float(v)

        return thresholds

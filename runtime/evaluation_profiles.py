"""Evaluation profiles — agent-specific weights and thresholds for self-evaluation.

Each profile defines how to weight different quality metrics (readability, linter,
accessibility, voice) and what composite score is required to pass evaluation.
"""

from __future__ import annotations

from typing import Any


EVALUATION_PROFILES: dict[str, dict[str, Any]] = {
    "cta-optimization-specialist": {
        "weights": {"readability": 0.3, "linter": 0.4, "voice": 0.3},
        "thresholds": {"composite_score": 80, "readability_min": 65},
    },
    "accessibility-content-auditor": {
        "weights": {"accessibility": 0.7, "readability": 0.2, "linter": 0.1},
        "thresholds": {"composite_score": 85, "accessibility_min": 90},
    },
    "localization-content-strategist": {
        "weights": {"readability": 0.5, "linter": 0.3, "voice": 0.2},
        "thresholds": {"composite_score": 75, "readability_min": 70},
    },
    "technical-documentation-writer": {
        "weights": {"readability": 0.4, "linter": 0.6},
        "thresholds": {"composite_score": 75, "readability_min": 60},
    },
    "tone-evaluation-agent": {
        "weights": {"voice": 0.8, "readability": 0.2},
        "thresholds": {"composite_score": 80, "voice_min": 85},
    },
    "content-designer-generalist": {
        "weights": {"readability": 0.3, "linter": 0.3, "accessibility": 0.2, "voice": 0.2},
        "thresholds": {"composite_score": 75, "readability_min": 60},
    },
    "conversational-ai-designer": {
        "weights": {"readability": 0.3, "linter": 0.3, "voice": 0.4},
        "thresholds": {"composite_score": 75, "readability_min": 60},
    },
    "microcopy-review-agent": {
        "weights": {"readability": 0.3, "linter": 0.4, "voice": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 65},
    },
    "onboarding-flow-designer": {
        "weights": {"readability": 0.4, "accessibility": 0.3, "linter": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 65},
    },
    "mobile-ux-writer": {
        "weights": {"readability": 0.4, "accessibility": 0.3, "linter": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 70},
    },
    "notification-content-designer": {
        "weights": {"readability": 0.4, "linter": 0.3, "accessibility": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 65},
    },
    "privacy-legal-content-simplifier": {
        "weights": {"readability": 0.5, "linter": 0.3, "accessibility": 0.2},
        "thresholds": {"composite_score": 80, "readability_min": 70},
    },
    "empty-state-placeholder-specialist": {
        "weights": {"readability": 0.3, "voice": 0.4, "linter": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 60},
    },
    "search-experience-writer": {
        "weights": {"readability": 0.4, "linter": 0.3, "voice": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 65},
    },
    "information-architect": {
        "weights": {"readability": 0.5, "linter": 0.5},
        "thresholds": {"composite_score": 70, "readability_min": 55},
    },
    "content-consistency-checker": {
        "weights": {"linter": 0.4, "voice": 0.4, "readability": 0.2},
        "thresholds": {"composite_score": 80, "readability_min": 60},
    },
    "error-message-architect": {
        "weights": {"readability": 0.4, "linter": 0.3, "accessibility": 0.3},
        "thresholds": {"composite_score": 75, "readability_min": 60},
    },
    "brand-voice-archaeologist": {
        "weights": {"voice": 0.6, "readability": 0.2, "linter": 0.2},
        "thresholds": {"composite_score": 75, "readability_min": 55},
    },
    "default": {
        "weights": {"readability": 0.4, "linter": 0.3, "accessibility": 0.2, "voice": 0.1},
        "thresholds": {"composite_score": 70, "readability_min": 60},
    },
}


def get_evaluation_profile(agent_slug: str) -> dict[str, Any]:
    """Return the evaluation profile for an agent, falling back to default."""
    return EVALUATION_PROFILES.get(agent_slug, EVALUATION_PROFILES["default"])


def get_composite_threshold(agent_slug: str) -> float:
    """Return the composite score threshold for an agent."""
    profile = get_evaluation_profile(agent_slug)
    return profile["thresholds"].get("composite_score", 70)


def get_weights(agent_slug: str) -> dict[str, float]:
    """Return the metric weights for an agent."""
    profile = get_evaluation_profile(agent_slug)
    return profile["weights"]

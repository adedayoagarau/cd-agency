"""Multi-model consensus evaluator — optional second-pass quality gate.

Follows a 3-stage pattern:
1. Independent evaluation by each available LLM
2. Confidence scoring via inter-model agreement
3. Consensus synthesis using configurable aggregation

Gracefully degrades when fewer models are available than required.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

from runtime.council_config import CouncilConfig

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ModelEvaluation:
    """Single model's evaluation result."""

    model_name: str
    scores: dict[str, float] = field(default_factory=dict)
    reasoning: str = ""
    composite_score: float = 0.0
    evaluation_time: float = 0.0
    success: bool = True
    error: str | None = None


@dataclass
class CouncilResult:
    """Final consensus result from council evaluation."""

    consensus_scores: dict[str, float] = field(default_factory=dict)
    consensus_composite: float = 0.0
    confidence: float = 0.0
    participating_models: list[str] = field(default_factory=list)
    individual_evaluations: list[ModelEvaluation] = field(default_factory=list)
    synthesis_reasoning: str = ""
    total_time: float = 0.0
    quorum_met: bool = False
    fallback_used: bool = False


# ---------------------------------------------------------------------------
# Council evaluator
# ---------------------------------------------------------------------------

class CouncilEvaluator:
    """Multi-model consensus evaluator.

    Stages:
        1. Independent evaluation by each model
        2. Confidence scoring (variance-based agreement)
        3. Consensus synthesis with configurable method
    """

    def __init__(
        self,
        model_router: Any,
        config: CouncilConfig,
    ) -> None:
        self.model_router = model_router
        self.config = config
        self._cache: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        content: str,
        evaluation_profile: dict[str, float],
        context: dict[str, Any] | None = None,
    ) -> CouncilResult:
        """Run council evaluation on content.

        Args:
            content: Text to evaluate.
            evaluation_profile: Criteria weights (e.g. {"readability": 0.4, ...}).
            context: Optional extra context (brand_context, etc.).

        Returns:
            CouncilResult with consensus scores and metadata.
        """
        start_time = time.time()
        context = context or {}

        # Check cache
        cache_key = self._cache_key(content, evaluation_profile)
        if self.config.enable_caching and cache_key in self._cache:
            cached = self._cache[cache_key]
            if time.time() - cached["timestamp"] < self.config.cache_ttl_seconds:
                logger.debug("Using cached council evaluation")
                return cached["result"]

        # Get available models
        available = self.config.get_available_models(self.model_router)
        if len(available) < self.config.min_models:
            logger.warning(
                "Only %d models available, need %d for council",
                len(available),
                self.config.min_models,
            )
            return self._fallback(content, evaluation_profile, context, start_time)

        try:
            # Stage 1: Independent evaluation
            evaluations = self._stage_independent(
                content, evaluation_profile, available, context
            )
            successful = [e for e in evaluations if e.success]

            if len(successful) < self.config.min_quorum:
                logger.warning(
                    "%d/%d evaluations succeeded, quorum requires %d",
                    len(successful),
                    len(evaluations),
                    self.config.min_quorum,
                )
                return self._fallback(content, evaluation_profile, context, start_time)

            # Stage 2: Confidence scoring
            confidence = self._calculate_confidence(successful)

            # Stage 3: Consensus synthesis
            consensus = self._synthesize(successful, evaluation_profile, confidence)

            result = CouncilResult(
                consensus_scores=consensus["scores"],
                consensus_composite=consensus["composite"],
                confidence=confidence,
                participating_models=[e.model_name for e in successful],
                individual_evaluations=evaluations,
                synthesis_reasoning=consensus["reasoning"],
                total_time=time.time() - start_time,
                quorum_met=True,
            )

            # Cache
            if self.config.enable_caching:
                self._cache[cache_key] = {"result": result, "timestamp": time.time()}

            return result

        except Exception as e:
            logger.error("Council evaluation failed: %s", e)
            return self._fallback(content, evaluation_profile, context, start_time)

    # ------------------------------------------------------------------
    # Stage 1: Independent evaluation
    # ------------------------------------------------------------------

    def _stage_independent(
        self,
        content: str,
        evaluation_profile: dict[str, float],
        models: list[tuple[str, str]],
        context: dict[str, Any],
    ) -> list[ModelEvaluation]:
        """Evaluate content independently with each model."""
        with ThreadPoolExecutor(max_workers=self.config.max_parallel) as pool:
            futures = {
                pool.submit(
                    self._evaluate_single,
                    content,
                    evaluation_profile,
                    provider_key,
                    model_name,
                    context,
                ): model_name
                for provider_key, model_name in models
            }

            results: list[ModelEvaluation] = []
            for future in as_completed(futures, timeout=self.config.timeout_seconds):
                model_name = futures[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    logger.error("Model %s failed: %s", model_name, e)
                    results.append(
                        ModelEvaluation(
                            model_name=model_name,
                            success=False,
                            error=str(e),
                        )
                    )

            return results

    def _evaluate_single(
        self,
        content: str,
        evaluation_profile: dict[str, float],
        provider_key: str,
        model_name: str,
        context: dict[str, Any],
    ) -> ModelEvaluation:
        """Evaluate content with a single model via the router's provider."""
        start = time.time()

        try:
            provider = self.model_router._providers[provider_key]
            prompt = self._build_prompt(content, evaluation_profile, context)

            response = provider.complete(
                model=model_name,
                system="You are an expert content quality evaluator. Respond only in JSON.",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1,
            )

            scores, reasoning, composite = self._parse_response(
                response.content, evaluation_profile
            )

            return ModelEvaluation(
                model_name=model_name,
                scores=scores,
                reasoning=reasoning,
                composite_score=composite,
                evaluation_time=time.time() - start,
            )

        except Exception as e:
            return ModelEvaluation(
                model_name=model_name,
                evaluation_time=time.time() - start,
                success=False,
                error=str(e),
            )

    # ------------------------------------------------------------------
    # Stage 2: Confidence scoring
    # ------------------------------------------------------------------

    def _calculate_confidence(self, evaluations: list[ModelEvaluation]) -> float:
        """Calculate confidence from inter-model agreement (0–1)."""
        if len(evaluations) < 2:
            return 0.5

        composites = [e.composite_score for e in evaluations]
        if len(set(composites)) == 1:
            return 1.0

        variance = statistics.variance(composites)
        # Map variance to confidence — higher variance → lower confidence
        return max(0.0, min(1.0, 1.0 - variance * 4))

    # ------------------------------------------------------------------
    # Stage 3: Consensus synthesis
    # ------------------------------------------------------------------

    def _synthesize(
        self,
        evaluations: list[ModelEvaluation],
        evaluation_profile: dict[str, float],
        confidence: float,
    ) -> dict[str, Any]:
        """Combine individual evaluations into consensus."""
        # Collect scores per criterion
        by_criterion: dict[str, list[float]] = {}
        for criterion in evaluation_profile:
            scores = [e.scores.get(criterion, 0.5) for e in evaluations]
            by_criterion[criterion] = scores

        # Aggregate
        consensus_scores: dict[str, float] = {}
        for criterion, scores in by_criterion.items():
            if self.config.consensus_method == "mean":
                consensus_scores[criterion] = statistics.mean(scores)
            elif self.config.consensus_method == "median":
                consensus_scores[criterion] = statistics.median(scores)
            else:  # weighted_median — use median as a good default
                consensus_scores[criterion] = statistics.median(scores)

        # Composite
        composite = sum(
            consensus_scores.get(c, 0.5) * w
            for c, w in evaluation_profile.items()
        )

        # Reasoning
        model_count = len(evaluations)
        parts = [f"Council evaluation from {model_count} models (confidence: {confidence:.2f})"]
        for criterion, score in consensus_scores.items():
            scores = by_criterion[criterion]
            spread = max(scores) - min(scores)
            agreement = "models agreed" if spread <= 0.3 else "models varied significantly"
            parts.append(f"{criterion}: {score:.2f} ({agreement})")

        return {
            "scores": consensus_scores,
            "composite": round(composite, 4),
            "reasoning": "; ".join(parts),
        }

    # ------------------------------------------------------------------
    # Fallback
    # ------------------------------------------------------------------

    def _fallback(
        self,
        content: str,
        evaluation_profile: dict[str, float],
        context: dict[str, Any],
        start_time: float,
    ) -> CouncilResult:
        """Fall back to single-model evaluation or neutral scores."""
        available = self.config.get_available_models(self.model_router)

        if not available:
            neutral = {c: 0.5 for c in evaluation_profile}
            composite = sum(neutral[c] * w for c, w in evaluation_profile.items())
            return CouncilResult(
                consensus_scores=neutral,
                consensus_composite=round(composite, 4),
                confidence=0.0,
                synthesis_reasoning="No models available for council evaluation",
                total_time=time.time() - start_time,
                fallback_used=True,
            )

        provider_key, model_name = available[0]
        evaluation = self._evaluate_single(
            content, evaluation_profile, provider_key, model_name, context
        )

        return CouncilResult(
            consensus_scores=evaluation.scores,
            consensus_composite=evaluation.composite_score,
            confidence=0.5,
            participating_models=[model_name] if evaluation.success else [],
            individual_evaluations=[evaluation],
            synthesis_reasoning=f"Fallback evaluation using {model_name}",
            total_time=time.time() - start_time,
            fallback_used=True,
        )

    # ------------------------------------------------------------------
    # Prompt & parsing
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        content: str,
        evaluation_profile: dict[str, float],
        context: dict[str, Any],
    ) -> str:
        """Build a standardized evaluation prompt."""
        criteria_lines = "\n".join(
            f"- {c.replace('_', ' ').title()}: weight {w:.2f}"
            for c, w in evaluation_profile.items()
        )

        brand_ctx = context.get("brand_context", "")
        brand_section = f"\nBrand Context:\n{brand_ctx}\n" if brand_ctx else ""

        score_keys = ", ".join(f'"{c}": 0.0' for c in evaluation_profile)

        return (
            "Evaluate the following content across these criteria:\n\n"
            f"EVALUATION CRITERIA:\n{criteria_lines}\n\n"
            f"CONTENT TO EVALUATE:\n{content}\n"
            f"{brand_section}\n"
            "Score each criterion from 0.0 to 1.0 (1.0 = excellent).\n"
            "Respond in this exact JSON format:\n"
            "{\n"
            f'    "scores": {{{score_keys}}},\n'
            '    "composite_score": 0.0,\n'
            '    "reasoning": "brief explanation"\n'
            "}"
        )

    def _parse_response(
        self,
        response_text: str,
        evaluation_profile: dict[str, float],
    ) -> tuple[dict[str, float], str, float]:
        """Parse LLM evaluation response into scores."""
        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(response_text[json_start:json_end])
            else:
                data = json.loads(response_text)

            scores = data.get("scores", {})
            # Validate and clamp scores
            for criterion in evaluation_profile:
                if criterion not in scores:
                    scores[criterion] = 0.5
                else:
                    scores[criterion] = max(0.0, min(1.0, float(scores[criterion])))

            composite = data.get("composite_score", 0.0)
            if not composite or composite < 0 or composite > 1:
                composite = sum(
                    scores.get(c, 0.5) * w for c, w in evaluation_profile.items()
                )

            reasoning = data.get("reasoning", "")
            return scores, reasoning, composite

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to parse evaluation response: %s", e)
            # Fallback: try to find any number
            numbers = re.findall(r"[-+]?\d*\.?\d+", response_text)
            score = max(0.0, min(1.0, float(numbers[0]))) if numbers else 0.5

            scores = {c: score for c in evaluation_profile}
            composite = sum(scores[c] * w for c, w in evaluation_profile.items())
            return scores, "Failed to parse detailed evaluation", composite

    # ------------------------------------------------------------------
    # Caching
    # ------------------------------------------------------------------

    def _cache_key(self, content: str, profile: dict[str, float]) -> str:
        """Generate a deterministic cache key."""
        h1 = hashlib.md5(content.encode()).hexdigest()[:8]
        h2 = hashlib.md5(str(sorted(profile.items())).encode()).hexdigest()[:8]
        return f"{h1}_{h2}"

    def clear_cache(self) -> int:
        """Clear the evaluation cache. Returns entries removed."""
        n = len(self._cache)
        self._cache.clear()
        return n

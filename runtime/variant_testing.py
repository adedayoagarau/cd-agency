"""Content variant testing — generate, score, compare, and recommend.

Enables A/B (and A/B/C) content variant generation:
- VariantGenerator: Uses agents to produce multiple content alternatives
- VariantScorer: Scores each variant using existing quality tools
- VariantComparator: Compares variants and explains tradeoffs
- VariantSet: Collection of scored variants with recommendation
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


_VARIANTS_DIR = ".cd-agency/variants"
_MAX_VARIANT_SETS = 100


@dataclass
class ContentVariant:
    """A single content variant with scores and metadata."""

    id: str = ""
    label: str = ""  # "A", "B", "C" or custom
    content: str = ""
    agent_slug: str = ""
    agent_name: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    composite_score: float = 0.0
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    generation_params: dict[str, Any] = field(default_factory=dict)
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]


@dataclass
class VariantComparison:
    """Comparison between variants with tradeoff analysis."""

    dimensions: dict[str, dict[str, float]] = field(default_factory=dict)
    winner: str = ""  # variant label
    winner_reasoning: str = ""
    tradeoffs: list[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class VariantSet:
    """Collection of variants for a single content request."""

    id: str = ""
    timestamp: float = 0.0
    prompt: str = ""
    agent_slug: str = ""
    variants: list[ContentVariant] = field(default_factory=list)
    comparison: VariantComparison | None = None
    recommended_variant: str = ""  # variant label
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.timestamp:
            self.timestamp = time.time()

    @property
    def best(self) -> ContentVariant | None:
        """Return the highest-scoring variant."""
        if not self.variants:
            return None
        return max(self.variants, key=lambda v: v.composite_score)

    def get_variant(self, label: str) -> ContentVariant | None:
        """Get variant by label."""
        for v in self.variants:
            if v.label == label:
                return v
        return None


class VariantGenerator:
    """Generates multiple content variants using agents."""

    def __init__(self, runner: Any, registry: Any) -> None:
        self.runner = runner
        self.registry = registry

    def generate(
        self,
        agent_slug: str,
        user_input: dict[str, Any],
        n_variants: int = 3,
        *,
        temperature_range: tuple[float, float] = (0.5, 0.9),
        labels: list[str] | None = None,
    ) -> list[ContentVariant]:
        """Generate N variants using the same agent with different temperatures.

        Args:
            agent_slug: Agent to use for generation.
            user_input: Input fields for the agent.
            n_variants: Number of variants to generate (2-5).
            temperature_range: (min, max) temperature range.
            labels: Custom labels for variants (defaults to A, B, C...).

        Returns:
            List of ContentVariant objects.
        """
        n_variants = max(2, min(5, n_variants))
        agent = self.registry.get(agent_slug)
        if agent is None:
            return []

        if labels is None:
            labels = [chr(65 + i) for i in range(n_variants)]  # A, B, C, ...

        # Calculate temperatures
        if n_variants == 1:
            temperatures = [temperature_range[0]]
        else:
            step = (temperature_range[1] - temperature_range[0]) / (n_variants - 1)
            temperatures = [
                round(temperature_range[0] + i * step, 2) for i in range(n_variants)
            ]

        variants: list[ContentVariant] = []
        for i, (label, temp) in enumerate(zip(labels, temperatures)):
            try:
                output = self.runner.run(
                    agent, user_input, temperature=temp
                )
                variant = ContentVariant(
                    label=label,
                    content=output.content,
                    agent_slug=agent_slug,
                    agent_name=output.agent_name,
                    generation_params={"temperature": temp, "variant_index": i},
                    input_tokens=output.input_tokens,
                    output_tokens=output.output_tokens,
                    latency_ms=output.latency_ms,
                )
                variants.append(variant)
            except Exception as e:
                variants.append(
                    ContentVariant(
                        label=label,
                        agent_slug=agent_slug,
                        generation_params={"temperature": temp, "error": str(e)},
                    )
                )

        return variants

    def generate_multi_agent(
        self,
        agent_slugs: list[str],
        user_input: dict[str, Any],
    ) -> list[ContentVariant]:
        """Generate variants using different agents for the same prompt."""
        variants: list[ContentVariant] = []
        labels = [chr(65 + i) for i in range(len(agent_slugs))]

        for label, slug in zip(labels, agent_slugs):
            agent = self.registry.get(slug)
            if agent is None:
                continue

            try:
                output = self.runner.run(agent, user_input)
                variant = ContentVariant(
                    label=label,
                    content=output.content,
                    agent_slug=slug,
                    agent_name=output.agent_name,
                    generation_params={"multi_agent": True},
                    input_tokens=output.input_tokens,
                    output_tokens=output.output_tokens,
                    latency_ms=output.latency_ms,
                )
                variants.append(variant)
            except Exception:
                pass

        return variants


class VariantScorer:
    """Scores content variants using existing quality tools."""

    def score(self, variant: ContentVariant) -> ContentVariant:
        """Score a single variant and populate its scores field."""
        content = variant.content
        if not content:
            return variant

        scores: dict[str, float] = {}
        strengths: list[str] = []
        weaknesses: list[str] = []

        # Readability
        try:
            from tools.readability import analyze
            result = analyze(content)
            ease = result.get("flesch_reading_ease", 0)
            scores["readability"] = ease
            if ease >= 70:
                strengths.append(f"Good readability (Flesch: {ease:.0f})")
            elif ease < 50:
                weaknesses.append(f"Low readability (Flesch: {ease:.0f})")
        except Exception:
            pass

        # Linter
        try:
            from tools.linter import lint
            issues = lint(content)
            issue_list = issues if isinstance(issues, list) else []
            issue_count = len(issue_list)
            scores["lint_issues"] = issue_count
            lint_score = max(0, 100 - issue_count * 10)
            scores["lint_score"] = lint_score
            if issue_count == 0:
                strengths.append("No lint issues")
            else:
                weaknesses.append(f"{issue_count} lint issue(s)")
        except Exception:
            pass

        # Character count analysis
        char_count = len(content)
        word_count = len(content.split())
        scores["char_count"] = char_count
        scores["word_count"] = word_count
        if word_count <= 30:
            strengths.append(f"Concise ({word_count} words)")
        elif word_count > 100:
            weaknesses.append(f"Verbose ({word_count} words)")

        # Composite score
        score_values = []
        if "readability" in scores:
            score_values.append(min(100, max(0, scores["readability"])))
        if "lint_score" in scores:
            score_values.append(scores["lint_score"])

        variant.scores = scores
        variant.composite_score = sum(score_values) / len(score_values) if score_values else 0
        variant.strengths = strengths
        variant.weaknesses = weaknesses

        return variant

    def score_all(self, variants: list[ContentVariant]) -> list[ContentVariant]:
        """Score all variants in a list."""
        return [self.score(v) for v in variants]


class VariantComparator:
    """Compares scored variants and produces a recommendation."""

    def compare(self, variants: list[ContentVariant]) -> VariantComparison:
        """Compare variants and produce a recommendation with tradeoffs."""
        if not variants:
            return VariantComparison(recommendation="No variants to compare.")

        if len(variants) == 1:
            v = variants[0]
            return VariantComparison(
                winner=v.label,
                winner_reasoning="Only one variant generated.",
                recommendation=f"Variant {v.label} (score: {v.composite_score:.0f})",
            )

        # Build dimension comparison
        dimensions: dict[str, dict[str, float]] = {}
        for v in variants:
            for metric, value in v.scores.items():
                if metric not in dimensions:
                    dimensions[metric] = {}
                dimensions[metric][v.label] = value

        # Find winner
        best = max(variants, key=lambda v: v.composite_score)
        runner_up = sorted(variants, key=lambda v: v.composite_score, reverse=True)
        second = runner_up[1] if len(runner_up) > 1 else None

        # Analyze tradeoffs
        tradeoffs: list[str] = []
        if second:
            for metric, scores in dimensions.items():
                if metric in ("char_count", "word_count", "lint_issues"):
                    continue  # Skip raw counts
                best_score = scores.get(best.label, 0)
                second_score = scores.get(second.label, 0)
                if second_score > best_score:
                    tradeoffs.append(
                        f"Variant {second.label} scores higher on {metric} "
                        f"({second_score:.0f} vs {best_score:.0f})"
                    )

        # Reasoning
        reasoning_parts = [f"Highest composite score: {best.composite_score:.0f}/100"]
        if best.strengths:
            reasoning_parts.append(f"Strengths: {', '.join(best.strengths[:3])}")
        if best.weaknesses:
            reasoning_parts.append(f"Weaknesses: {', '.join(best.weaknesses[:2])}")

        # Recommendation
        rec_parts = [f"Recommended: Variant {best.label} (score: {best.composite_score:.0f})"]
        if tradeoffs:
            rec_parts.append("However, consider:")
            for t in tradeoffs[:3]:
                rec_parts.append(f"  - {t}")

        return VariantComparison(
            dimensions=dimensions,
            winner=best.label,
            winner_reasoning=". ".join(reasoning_parts),
            tradeoffs=tradeoffs,
            recommendation="\n".join(rec_parts),
        )


class VariantTestRunner:
    """End-to-end variant testing: generate → score → compare → recommend."""

    def __init__(self, runner: Any, registry: Any) -> None:
        self.generator = VariantGenerator(runner, registry)
        self.scorer = VariantScorer()
        self.comparator = VariantComparator()
        self._history: list[VariantSet] | None = None

    def test(
        self,
        agent_slug: str,
        user_input: dict[str, Any],
        n_variants: int = 3,
        *,
        temperature_range: tuple[float, float] = (0.5, 0.9),
    ) -> VariantSet:
        """Run a complete variant test.

        Generates N variants, scores them, compares, and recommends.
        """
        # Generate
        variants = self.generator.generate(
            agent_slug, user_input, n_variants,
            temperature_range=temperature_range,
        )

        # Score
        scored = self.scorer.score_all(variants)

        # Compare
        comparison = self.comparator.compare(scored)

        # Build result
        prompt = str(user_input.get(list(user_input.keys())[0], "")) if user_input else ""
        variant_set = VariantSet(
            prompt=prompt[:200],
            agent_slug=agent_slug,
            variants=scored,
            comparison=comparison,
            recommended_variant=comparison.winner,
        )

        return variant_set

    def test_multi_agent(
        self,
        agent_slugs: list[str],
        user_input: dict[str, Any],
    ) -> VariantSet:
        """Generate variants using different agents, score and compare."""
        variants = self.generator.generate_multi_agent(agent_slugs, user_input)
        scored = self.scorer.score_all(variants)
        comparison = self.comparator.compare(scored)

        prompt = str(user_input.get(list(user_input.keys())[0], "")) if user_input else ""
        return VariantSet(
            prompt=prompt[:200],
            agent_slug=",".join(agent_slugs),
            variants=scored,
            comparison=comparison,
            recommended_variant=comparison.winner,
        )

    def save_result(self, variant_set: VariantSet, project_dir: Path | str | None = None) -> None:
        """Save a variant test result to disk."""
        project_dir = Path(project_dir) if project_dir else Path(".")
        save_dir = project_dir / _VARIANTS_DIR
        save_dir.mkdir(parents=True, exist_ok=True)

        # Convert to serializable dict
        data = asdict(variant_set)
        save_path = save_dir / f"{variant_set.id}.json"
        save_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    @staticmethod
    def list_results(project_dir: Path | str | None = None) -> list[dict[str, Any]]:
        """List saved variant test results."""
        project_dir = Path(project_dir) if project_dir else Path(".")
        save_dir = project_dir / _VARIANTS_DIR

        if not save_dir.exists():
            return []

        results: list[dict[str, Any]] = []
        for f in sorted(save_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:_MAX_VARIANT_SETS]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                results.append({
                    "id": data.get("id", f.stem),
                    "timestamp": data.get("timestamp", 0),
                    "agent_slug": data.get("agent_slug", ""),
                    "prompt": data.get("prompt", "")[:80],
                    "variant_count": len(data.get("variants", [])),
                    "recommended": data.get("recommended_variant", ""),
                })
            except (json.JSONDecodeError, OSError):
                continue

        return results

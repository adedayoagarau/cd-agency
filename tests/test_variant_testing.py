"""Tests for content variant testing system."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput
from runtime.variant_testing import (
    ContentVariant,
    VariantComparator,
    VariantComparison,
    VariantGenerator,
    VariantScorer,
    VariantSet,
    VariantTestRunner,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_runner():
    call_count = [0]

    def _run(agent, user_input, **kwargs):
        call_count[0] += 1
        temp = kwargs.get("temperature", 0.7)
        return AgentOutput(
            content=f"Variant content at temp={temp:.2f}. Call #{call_count[0]}.",
            agent_name=agent.name,
            model="test-model",
            input_tokens=50,
            output_tokens=30,
            latency_ms=100,
        )

    runner = MagicMock()
    runner.run.side_effect = _run
    return runner


@pytest.fixture
def mock_registry():
    def _get(slug):
        return Agent(
            name=slug.replace("-", " ").title(),
            description=f"Agent {slug}",
            inputs=[AgentInput(name="content", type="string", required=True)],
            system_prompt=f"You are {slug}.",
            source_file=f"{slug}.md",
        )

    registry = MagicMock()
    registry.get = _get
    return registry


# ---------------------------------------------------------------------------
# ContentVariant
# ---------------------------------------------------------------------------

class TestContentVariant:
    def test_defaults(self):
        v = ContentVariant(label="A", content="test")
        assert v.id != ""
        assert v.label == "A"

    def test_empty(self):
        v = ContentVariant()
        assert v.content == ""
        assert v.composite_score == 0.0


# ---------------------------------------------------------------------------
# VariantSet
# ---------------------------------------------------------------------------

class TestVariantSet:
    def test_best_variant(self):
        vs = VariantSet(
            variants=[
                ContentVariant(label="A", content="a", composite_score=60),
                ContentVariant(label="B", content="b", composite_score=85),
                ContentVariant(label="C", content="c", composite_score=70),
            ]
        )
        assert vs.best.label == "B"

    def test_best_empty(self):
        vs = VariantSet()
        assert vs.best is None

    def test_get_variant(self):
        vs = VariantSet(
            variants=[
                ContentVariant(label="A", content="a"),
                ContentVariant(label="B", content="b"),
            ]
        )
        assert vs.get_variant("B").content == "b"
        assert vs.get_variant("Z") is None


# ---------------------------------------------------------------------------
# VariantGenerator
# ---------------------------------------------------------------------------

class TestVariantGenerator:
    def test_generate_default(self, mock_runner, mock_registry):
        gen = VariantGenerator(mock_runner, mock_registry)
        variants = gen.generate(
            "content-designer-generalist",
            {"content": "Write a button label"},
        )

        assert len(variants) == 3
        assert variants[0].label == "A"
        assert variants[1].label == "B"
        assert variants[2].label == "C"
        assert all(v.content for v in variants)

    def test_generate_custom_count(self, mock_runner, mock_registry):
        gen = VariantGenerator(mock_runner, mock_registry)
        variants = gen.generate(
            "content-designer-generalist",
            {"content": "test"},
            n_variants=2,
        )
        assert len(variants) == 2

    def test_generate_capped_at_5(self, mock_runner, mock_registry):
        gen = VariantGenerator(mock_runner, mock_registry)
        variants = gen.generate(
            "content-designer-generalist",
            {"content": "test"},
            n_variants=10,
        )
        assert len(variants) == 5

    def test_generate_min_2(self, mock_runner, mock_registry):
        gen = VariantGenerator(mock_runner, mock_registry)
        variants = gen.generate(
            "content-designer-generalist",
            {"content": "test"},
            n_variants=1,
        )
        assert len(variants) == 2

    def test_generate_agent_not_found(self, mock_runner):
        registry = MagicMock()
        registry.get.return_value = None

        gen = VariantGenerator(mock_runner, registry)
        variants = gen.generate("nonexistent", {"content": "test"})
        assert variants == []

    def test_generate_custom_labels(self, mock_runner, mock_registry):
        gen = VariantGenerator(mock_runner, mock_registry)
        variants = gen.generate(
            "content-designer-generalist",
            {"content": "test"},
            n_variants=2,
            labels=["Formal", "Casual"],
        )
        assert variants[0].label == "Formal"
        assert variants[1].label == "Casual"

    def test_generate_multi_agent(self, mock_runner, mock_registry):
        gen = VariantGenerator(mock_runner, mock_registry)
        variants = gen.generate_multi_agent(
            ["content-designer-generalist", "error-message-architect"],
            {"content": "Write an error message"},
        )
        assert len(variants) == 2
        assert variants[0].agent_slug == "content-designer-generalist"
        assert variants[1].agent_slug == "error-message-architect"

    def test_generate_handles_error(self, mock_registry):
        runner = MagicMock()
        runner.run.side_effect = Exception("API Error")

        gen = VariantGenerator(runner, mock_registry)
        variants = gen.generate(
            "content-designer-generalist",
            {"content": "test"},
            n_variants=2,
        )
        # Should still return variants (with empty content)
        assert len(variants) == 2


# ---------------------------------------------------------------------------
# VariantScorer
# ---------------------------------------------------------------------------

class TestVariantScorer:
    def test_score_empty_content(self):
        scorer = VariantScorer()
        v = ContentVariant(label="A", content="")
        scored = scorer.score(v)
        assert scored.composite_score == 0.0

    def test_score_with_content(self):
        scorer = VariantScorer()
        v = ContentVariant(
            label="A",
            content="This is a simple and clear test message for users.",
        )
        scored = scorer.score(v)
        assert "word_count" in scored.scores
        assert "char_count" in scored.scores

    def test_score_all(self):
        scorer = VariantScorer()
        variants = [
            ContentVariant(label="A", content="Short text."),
            ContentVariant(label="B", content="This is a longer piece of content."),
        ]
        scored = scorer.score_all(variants)
        assert len(scored) == 2
        assert all(v.scores for v in scored)


# ---------------------------------------------------------------------------
# VariantComparator
# ---------------------------------------------------------------------------

class TestVariantComparator:
    def test_compare_empty(self):
        comp = VariantComparator()
        result = comp.compare([])
        assert "No variants" in result.recommendation

    def test_compare_single(self):
        comp = VariantComparator()
        result = comp.compare([
            ContentVariant(label="A", content="only one", composite_score=80),
        ])
        assert result.winner == "A"
        assert "Only one" in result.winner_reasoning

    def test_compare_multiple(self):
        comp = VariantComparator()
        result = comp.compare([
            ContentVariant(
                label="A", content="a",
                composite_score=70,
                scores={"readability": 80, "lint_score": 60},
                strengths=["Clear"],
            ),
            ContentVariant(
                label="B", content="b",
                composite_score=85,
                scores={"readability": 75, "lint_score": 95},
                strengths=["Concise"],
            ),
        ])
        assert result.winner == "B"
        assert "85" in result.recommendation

    def test_compare_tradeoffs(self):
        comp = VariantComparator()
        result = comp.compare([
            ContentVariant(
                label="A", content="a",
                composite_score=85,
                scores={"readability": 70, "lint_score": 100},
            ),
            ContentVariant(
                label="B", content="b",
                composite_score=80,
                scores={"readability": 95, "lint_score": 65},
            ),
        ])
        assert result.winner == "A"
        # B scores higher on readability — should appear in tradeoffs
        assert len(result.tradeoffs) >= 1


# ---------------------------------------------------------------------------
# VariantTestRunner
# ---------------------------------------------------------------------------

class TestVariantTestRunner:
    def test_full_test(self, mock_runner, mock_registry):
        tester = VariantTestRunner(mock_runner, mock_registry)
        result = tester.test(
            "content-designer-generalist",
            {"content": "Write a button label"},
            n_variants=2,
        )

        assert isinstance(result, VariantSet)
        assert len(result.variants) == 2
        assert result.comparison is not None
        assert result.recommended_variant != ""

    def test_multi_agent_test(self, mock_runner, mock_registry):
        tester = VariantTestRunner(mock_runner, mock_registry)
        result = tester.test_multi_agent(
            ["content-designer-generalist", "cta-optimization-specialist"],
            {"content": "Write a CTA"},
        )

        assert len(result.variants) == 2
        assert result.comparison is not None

    def test_save_and_list(self, mock_runner, mock_registry, tmp_path):
        tester = VariantTestRunner(mock_runner, mock_registry)
        result = tester.test(
            "content-designer-generalist",
            {"content": "test"},
            n_variants=2,
        )

        tester.save_result(result, project_dir=tmp_path)
        results = tester.list_results(project_dir=tmp_path)
        assert len(results) == 1
        assert results[0]["variant_count"] == 2

    def test_list_results_empty(self, tmp_path):
        results = VariantTestRunner.list_results(project_dir=tmp_path)
        assert results == []

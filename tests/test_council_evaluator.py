"""Tests for the multi-model council evaluation system."""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from runtime.council_config import CouncilConfig
from runtime.council_evaluator import (
    CouncilEvaluator,
    CouncilResult,
    ModelEvaluation,
)


# ---------------------------------------------------------------------------
# CouncilConfig
# ---------------------------------------------------------------------------

class TestCouncilConfig:
    def test_defaults(self):
        config = CouncilConfig()
        assert config.enabled is False
        assert config.min_models == 2
        assert config.min_quorum == 2
        assert config.max_parallel == 3
        assert config.consensus_method == "weighted_median"
        assert config.confidence_threshold == 0.7
        assert "manual" in config.trigger_conditions
        assert config.enable_caching is True
        assert config.cache_ttl_seconds == 300

    def test_invalid_consensus_method(self):
        with pytest.raises(ValueError, match="Invalid consensus method"):
            CouncilConfig(consensus_method="invalid")

    def test_valid_consensus_methods(self):
        for method in ("weighted_median", "mean", "median"):
            config = CouncilConfig(consensus_method=method)
            assert config.consensus_method == method

    def test_from_config_missing_file(self, tmp_path):
        config = CouncilConfig.from_config(tmp_path / "nonexistent.yaml")
        assert config.enabled is False  # defaults

    def test_from_config_empty_council(self, tmp_path):
        import yaml

        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"global": {"composite_score": 75}}))
        config = CouncilConfig.from_config(cfg_file)
        assert config.enabled is False

    def test_from_config_with_values(self, tmp_path):
        import yaml

        data = {
            "council": {
                "enabled": True,
                "min_models": 3,
                "consensus_method": "mean",
                "timeout_seconds": 60.0,
                "trigger_conditions": ["always", "high_stakes"],
            }
        }
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump(data))

        config = CouncilConfig.from_config(cfg_file)
        assert config.enabled is True
        assert config.min_models == 3
        assert config.consensus_method == "mean"
        assert config.timeout_seconds == 60.0
        assert set(config.trigger_conditions) == {"always", "high_stakes"}

    def test_from_config_ignores_unknown_keys(self, tmp_path):
        import yaml

        data = {"council": {"enabled": True, "unknown_key": "ignored"}}
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump(data))

        config = CouncilConfig.from_config(cfg_file)
        assert config.enabled is True
        assert not hasattr(config, "unknown_key")

    def test_from_config_corrupt_yaml(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text("{{{invalid yaml")

        config = CouncilConfig.from_config(cfg_file)
        assert config.enabled is False  # defaults

    def test_loads_from_real_config(self):
        """Loads from the project's actual config file."""
        config = CouncilConfig.from_config()
        assert config.enabled is False  # disabled by default in project config


class TestCouncilConfigTrigger:
    def test_disabled_never_triggers(self):
        config = CouncilConfig(enabled=False, trigger_conditions=["always"])
        assert config.should_trigger({}) is False

    def test_always_triggers(self):
        config = CouncilConfig(enabled=True, trigger_conditions=["always"])
        assert config.should_trigger({}) is True

    def test_manual_requires_force(self):
        config = CouncilConfig(enabled=True, trigger_conditions=["manual"])
        assert config.should_trigger({}) is False
        assert config.should_trigger({"force_council": True}) is True

    def test_high_stakes(self):
        config = CouncilConfig(enabled=True, trigger_conditions=["high_stakes"])
        assert config.should_trigger({}) is False
        assert config.should_trigger({"high_stakes": True}) is True

    def test_low_confidence(self):
        config = CouncilConfig(
            enabled=True,
            trigger_conditions=["low_confidence"],
            confidence_threshold=0.7,
        )
        assert config.should_trigger({"single_model_confidence": 0.9}) is False
        assert config.should_trigger({"single_model_confidence": 0.5}) is True

    def test_quality_threshold_failed(self):
        config = CouncilConfig(
            enabled=True, trigger_conditions=["quality_threshold_failed"]
        )
        assert config.should_trigger({}) is False
        assert config.should_trigger({"quality_threshold_failed": True}) is True

    def test_multiple_conditions_any_match(self):
        config = CouncilConfig(
            enabled=True, trigger_conditions=["manual", "high_stakes"]
        )
        assert config.should_trigger({"high_stakes": True}) is True
        assert config.should_trigger({"force_council": True}) is True
        assert config.should_trigger({}) is False


class TestCouncilConfigAvailableModels:
    def test_no_providers(self):
        config = CouncilConfig()
        router = MagicMock()
        router._providers = {}
        assert config.get_available_models(router) == []

    def test_single_provider(self):
        config = CouncilConfig()
        provider = MagicMock()
        provider.is_available.return_value = True
        router = MagicMock()
        router._providers = {"anthropic": provider}

        available = config.get_available_models(router)
        assert len(available) == 1
        assert available[0][0] == "anthropic"

    def test_multiple_providers(self):
        config = CouncilConfig()
        providers = {}
        for name in ("anthropic", "openai", "openrouter"):
            p = MagicMock()
            p.is_available.return_value = True
            providers[name] = p

        router = MagicMock()
        router._providers = providers

        available = config.get_available_models(router)
        assert len(available) == 3

    def test_max_parallel_limits(self):
        config = CouncilConfig(max_parallel=2)
        providers = {}
        for name in ("anthropic", "openai", "openrouter"):
            p = MagicMock()
            p.is_available.return_value = True
            providers[name] = p

        router = MagicMock()
        router._providers = providers

        available = config.get_available_models(router)
        assert len(available) == 2

    def test_unavailable_provider_excluded(self):
        config = CouncilConfig()
        p1 = MagicMock()
        p1.is_available.return_value = True
        p2 = MagicMock()
        p2.is_available.return_value = False

        router = MagicMock()
        router._providers = {"anthropic": p1, "openai": p2}

        available = config.get_available_models(router)
        assert len(available) == 1
        assert available[0][0] == "anthropic"


# ---------------------------------------------------------------------------
# ModelEvaluation & CouncilResult
# ---------------------------------------------------------------------------

class TestDataStructures:
    def test_model_evaluation_defaults(self):
        e = ModelEvaluation(model_name="test-model")
        assert e.model_name == "test-model"
        assert e.scores == {}
        assert e.success is True
        assert e.error is None
        assert e.composite_score == 0.0

    def test_model_evaluation_failure(self):
        e = ModelEvaluation(
            model_name="test", success=False, error="Connection timeout"
        )
        assert e.success is False
        assert e.error == "Connection timeout"

    def test_council_result_defaults(self):
        r = CouncilResult()
        assert r.consensus_composite == 0.0
        assert r.confidence == 0.0
        assert r.quorum_met is False
        assert r.fallback_used is False
        assert r.participating_models == []


# ---------------------------------------------------------------------------
# CouncilEvaluator
# ---------------------------------------------------------------------------

def _make_router_with_providers(*provider_keys):
    """Create a mock router with the given provider keys."""
    router = MagicMock()
    providers = {}
    for key in provider_keys:
        p = MagicMock()
        p.is_available.return_value = True
        providers[key] = p
    router._providers = providers
    return router


def _make_provider_response(scores, composite=None, reasoning="Good"):
    """Create a mock provider that returns a JSON evaluation response."""
    if composite is None:
        composite = sum(scores.values()) / len(scores)
    response_json = json.dumps({
        "scores": scores,
        "composite_score": composite,
        "reasoning": reasoning,
    })
    provider = MagicMock()
    resp = MagicMock()
    resp.content = response_json
    provider.complete.return_value = resp
    return provider


class TestCouncilEvaluator:
    @pytest.fixture
    def profile(self):
        return {"readability": 0.4, "linter": 0.3, "voice": 0.3}

    def test_evaluate_insufficient_models(self, profile):
        """Falls back when fewer models than required."""
        router = _make_router_with_providers()  # no providers
        config = CouncilConfig(enabled=True, min_models=2)
        evaluator = CouncilEvaluator(router, config)

        result = evaluator.evaluate("test content", profile)

        assert result.fallback_used is True
        assert result.quorum_met is False

    def test_evaluate_successful_council(self, profile):
        """Full council evaluation with two models."""
        router = MagicMock()
        p1 = _make_provider_response(
            {"readability": 0.8, "linter": 0.9, "voice": 0.7}
        )
        p2 = _make_provider_response(
            {"readability": 0.7, "linter": 0.8, "voice": 0.8}
        )
        router._providers = {"anthropic": p1, "openai": p2}
        p1.is_available.return_value = True
        p2.is_available.return_value = True

        config = CouncilConfig(enabled=True, min_models=2, min_quorum=2)
        evaluator = CouncilEvaluator(router, config)

        result = evaluator.evaluate("test content", profile)

        assert result.quorum_met is True
        assert result.fallback_used is False
        assert len(result.participating_models) == 2
        assert 0.0 <= result.consensus_composite <= 1.0
        assert 0.0 <= result.confidence <= 1.0
        assert result.total_time > 0

    def test_evaluate_partial_failure(self, profile):
        """Falls back when not enough models succeed."""
        router = MagicMock()
        p1 = _make_provider_response(
            {"readability": 0.8, "linter": 0.9, "voice": 0.7}
        )
        p2 = MagicMock()
        p2.is_available.return_value = True
        p2.complete.side_effect = Exception("API error")
        router._providers = {"anthropic": p1, "openai": p2}
        p1.is_available.return_value = True

        config = CouncilConfig(enabled=True, min_models=2, min_quorum=2)
        evaluator = CouncilEvaluator(router, config)

        result = evaluator.evaluate("test content", profile)

        # One failed, quorum not met → fallback
        assert result.fallback_used is True

    def test_evaluate_single_model_fallback(self, profile):
        """Falls back to single model when only one available."""
        router = MagicMock()
        p1 = _make_provider_response(
            {"readability": 0.8, "linter": 0.9, "voice": 0.7}
        )
        p1.is_available.return_value = True
        router._providers = {"anthropic": p1}

        config = CouncilConfig(enabled=True, min_models=2)
        evaluator = CouncilEvaluator(router, config)

        result = evaluator.evaluate("test content", profile)

        assert result.fallback_used is True
        assert result.confidence == 0.5  # low confidence for single model

    def test_caching(self, profile):
        """Second call with same content uses cache."""
        router = MagicMock()
        p1 = _make_provider_response({"readability": 0.8, "linter": 0.9, "voice": 0.7})
        p2 = _make_provider_response({"readability": 0.7, "linter": 0.8, "voice": 0.8})
        p1.is_available.return_value = True
        p2.is_available.return_value = True
        router._providers = {"anthropic": p1, "openai": p2}

        config = CouncilConfig(enabled=True, min_models=2, enable_caching=True)
        evaluator = CouncilEvaluator(router, config)

        result1 = evaluator.evaluate("test content", profile)
        result2 = evaluator.evaluate("test content", profile)

        # Second call should use cache — providers called only for first eval
        assert p1.complete.call_count == 1
        assert result1.consensus_composite == result2.consensus_composite

    def test_caching_different_content(self, profile):
        """Different content produces different cache keys."""
        router = MagicMock()
        p1 = _make_provider_response({"readability": 0.8, "linter": 0.9, "voice": 0.7})
        p2 = _make_provider_response({"readability": 0.7, "linter": 0.8, "voice": 0.8})
        p1.is_available.return_value = True
        p2.is_available.return_value = True
        router._providers = {"anthropic": p1, "openai": p2}

        config = CouncilConfig(enabled=True, min_models=2, enable_caching=True)
        evaluator = CouncilEvaluator(router, config)

        evaluator.evaluate("content A", profile)
        evaluator.evaluate("content B", profile)

        # Both calls should hit providers
        assert p1.complete.call_count == 2

    def test_caching_disabled(self, profile):
        """No caching when disabled."""
        router = MagicMock()
        p1 = _make_provider_response({"readability": 0.8, "linter": 0.9, "voice": 0.7})
        p2 = _make_provider_response({"readability": 0.7, "linter": 0.8, "voice": 0.8})
        p1.is_available.return_value = True
        p2.is_available.return_value = True
        router._providers = {"anthropic": p1, "openai": p2}

        config = CouncilConfig(enabled=True, min_models=2, enable_caching=False)
        evaluator = CouncilEvaluator(router, config)

        evaluator.evaluate("test content", profile)
        evaluator.evaluate("test content", profile)

        assert p1.complete.call_count == 2

    def test_clear_cache(self, profile):
        """clear_cache removes all cached entries."""
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        evaluator = CouncilEvaluator(router, config)
        evaluator._cache["key1"] = {"result": None, "timestamp": time.time()}
        evaluator._cache["key2"] = {"result": None, "timestamp": time.time()}

        removed = evaluator.clear_cache()
        assert removed == 2
        assert len(evaluator._cache) == 0

    def test_cache_key_deterministic(self, profile):
        """Same inputs produce same cache key."""
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        evaluator = CouncilEvaluator(router, config)

        k1 = evaluator._cache_key("content", profile)
        k2 = evaluator._cache_key("content", profile)
        k3 = evaluator._cache_key("different content", profile)

        assert k1 == k2
        assert k1 != k3


class TestConfidenceScoring:
    def test_single_model_low_confidence(self):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        evaluator = CouncilEvaluator(router, config)

        evals = [ModelEvaluation(model_name="m1", composite_score=0.8)]
        assert evaluator._calculate_confidence(evals) == 0.5

    def test_perfect_agreement_high_confidence(self):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        evaluator = CouncilEvaluator(router, config)

        evals = [
            ModelEvaluation(model_name="m1", composite_score=0.8),
            ModelEvaluation(model_name="m2", composite_score=0.8),
        ]
        assert evaluator._calculate_confidence(evals) == 1.0

    def test_disagreement_lower_confidence(self):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        evaluator = CouncilEvaluator(router, config)

        evals = [
            ModelEvaluation(model_name="m1", composite_score=0.3),
            ModelEvaluation(model_name="m2", composite_score=0.9),
        ]
        confidence = evaluator._calculate_confidence(evals)
        assert confidence < 0.5  # significant disagreement

    def test_slight_disagreement_moderate_confidence(self):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        evaluator = CouncilEvaluator(router, config)

        evals = [
            ModelEvaluation(model_name="m1", composite_score=0.75),
            ModelEvaluation(model_name="m2", composite_score=0.85),
        ]
        confidence = evaluator._calculate_confidence(evals)
        assert 0.5 < confidence < 1.0


class TestConsensusSynthesis:
    @pytest.fixture
    def evaluator(self):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True, consensus_method="mean")
        return CouncilEvaluator(router, config)

    @pytest.fixture
    def profile(self):
        return {"readability": 0.5, "voice": 0.5}

    def test_mean_consensus(self, evaluator, profile):
        evals = [
            ModelEvaluation(
                model_name="m1", scores={"readability": 0.6, "voice": 0.8}
            ),
            ModelEvaluation(
                model_name="m2", scores={"readability": 0.8, "voice": 0.6}
            ),
        ]
        result = evaluator._synthesize(evals, profile, confidence=0.8)

        assert result["scores"]["readability"] == pytest.approx(0.7)
        assert result["scores"]["voice"] == pytest.approx(0.7)
        assert result["composite"] == pytest.approx(0.7, abs=0.01)

    def test_median_consensus(self, profile):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True, consensus_method="median")
        evaluator = CouncilEvaluator(router, config)

        evals = [
            ModelEvaluation(model_name="m1", scores={"readability": 0.6, "voice": 0.5}),
            ModelEvaluation(model_name="m2", scores={"readability": 0.8, "voice": 0.7}),
            ModelEvaluation(model_name="m3", scores={"readability": 0.9, "voice": 0.9}),
        ]
        result = evaluator._synthesize(evals, profile, confidence=0.7)

        assert result["scores"]["readability"] == 0.8  # median of 0.6, 0.8, 0.9
        assert result["scores"]["voice"] == 0.7  # median of 0.5, 0.7, 0.9

    def test_synthesis_reasoning_includes_model_count(self, evaluator, profile):
        evals = [
            ModelEvaluation(model_name="m1", scores={"readability": 0.7, "voice": 0.7}),
            ModelEvaluation(model_name="m2", scores={"readability": 0.7, "voice": 0.7}),
        ]
        result = evaluator._synthesize(evals, profile, confidence=0.9)

        assert "2 models" in result["reasoning"]
        assert "0.90" in result["reasoning"]

    def test_synthesis_flags_high_variance(self, evaluator, profile):
        evals = [
            ModelEvaluation(model_name="m1", scores={"readability": 0.3, "voice": 0.9}),
            ModelEvaluation(model_name="m2", scores={"readability": 0.9, "voice": 0.9}),
        ]
        result = evaluator._synthesize(evals, profile, confidence=0.5)

        assert "varied significantly" in result["reasoning"]

    def test_missing_criterion_defaults_to_half(self, evaluator, profile):
        evals = [
            ModelEvaluation(model_name="m1", scores={"readability": 0.8}),
            ModelEvaluation(model_name="m2", scores={"voice": 0.8}),
        ]
        result = evaluator._synthesize(evals, profile, confidence=0.5)

        # Missing scores default to 0.5
        assert "readability" in result["scores"]
        assert "voice" in result["scores"]


class TestResponseParsing:
    @pytest.fixture
    def evaluator(self):
        router = _make_router_with_providers()
        config = CouncilConfig(enabled=True)
        return CouncilEvaluator(router, config)

    @pytest.fixture
    def profile(self):
        return {"readability": 0.5, "voice": 0.5}

    def test_valid_json(self, evaluator, profile):
        response = json.dumps({
            "scores": {"readability": 0.85, "voice": 0.7},
            "composite_score": 0.775,
            "reasoning": "Well written",
        })
        scores, reasoning, composite = evaluator._parse_response(response, profile)

        assert scores["readability"] == 0.85
        assert scores["voice"] == 0.7
        assert composite == 0.775
        assert reasoning == "Well written"

    def test_json_embedded_in_text(self, evaluator, profile):
        response = 'Here is my evaluation:\n{"scores": {"readability": 0.9, "voice": 0.8}, "composite_score": 0.85, "reasoning": "Good"}\nDone.'
        scores, reasoning, composite = evaluator._parse_response(response, profile)

        assert scores["readability"] == 0.9
        assert scores["voice"] == 0.8

    def test_missing_criterion_defaults(self, evaluator, profile):
        response = json.dumps({
            "scores": {"readability": 0.9},
            "composite_score": 0.7,
            "reasoning": "Partial",
        })
        scores, _, _ = evaluator._parse_response(response, profile)

        assert scores["readability"] == 0.9
        assert scores["voice"] == 0.5  # defaulted

    def test_scores_clamped(self, evaluator, profile):
        response = json.dumps({
            "scores": {"readability": 1.5, "voice": -0.3},
            "composite_score": 0.6,
            "reasoning": "Out of range",
        })
        scores, _, _ = evaluator._parse_response(response, profile)

        assert scores["readability"] == 1.0  # clamped
        assert scores["voice"] == 0.0  # clamped

    def test_invalid_json_fallback(self, evaluator, profile):
        response = "This is not JSON at all"
        scores, reasoning, composite = evaluator._parse_response(response, profile)

        # Should return neutral scores
        assert scores["readability"] == 0.5
        assert scores["voice"] == 0.5
        assert "Failed to parse" in reasoning

    def test_invalid_json_with_number(self, evaluator, profile):
        response = "The overall score is 0.75 out of 1.0"
        scores, _, _ = evaluator._parse_response(response, profile)

        assert scores["readability"] == 0.75
        assert scores["voice"] == 0.75

    def test_invalid_composite_recalculated(self, evaluator, profile):
        response = json.dumps({
            "scores": {"readability": 0.8, "voice": 0.6},
            "composite_score": -5,  # invalid
            "reasoning": "Bad composite",
        })
        _, _, composite = evaluator._parse_response(response, profile)

        # Should recalculate: 0.8*0.5 + 0.6*0.5 = 0.7
        assert composite == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# ContentDesignGraph integration
# ---------------------------------------------------------------------------

class TestContentDesignGraphCouncil:
    def _make_graph(self, council_enabled=False):
        from runtime.agent import Agent, AgentInput
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter, ScoreReadability

        agent = Agent(
            name="Test Agent",
            description="test",
            inputs=[AgentInput(name="content", type="string", required=True)],
            available_tools=["run_linter", "score_readability"],
            system_prompt="You are a test agent.",
            source_file="test.md",
        )

        mock_router = MagicMock()
        mock_memory = MagicMock()
        mock_memory.get_context_for_agent.return_value = ""

        tools = [RunLinter(), ScoreReadability()]
        graph = ContentDesignGraph(
            agent=agent,
            tools=tools,
            model_router=mock_router,
            memory=mock_memory,
            model="test-model",
        )

        if council_enabled:
            # Manually inject council config and evaluator
            from runtime.council_config import CouncilConfig

            graph._council_config = CouncilConfig(
                enabled=True, trigger_conditions=["always"]
            )
            mock_evaluator = MagicMock()
            mock_result = CouncilResult(
                consensus_scores={"readability": 0.8, "linter": 0.9},
                consensus_composite=0.85,
                confidence=0.9,
                participating_models=["model-a", "model-b"],
                quorum_met=True,
                synthesis_reasoning="Good consensus",
            )
            mock_evaluator.evaluate.return_value = mock_result
            graph._council_evaluator = mock_evaluator

        return graph

    def test_evaluate_without_council(self):
        """Council disabled — no _council key in scores."""
        graph = self._make_graph(council_enabled=False)
        state = {"current_output": "Click here to try again."}

        result = graph._node_evaluate(state)
        scores = result["evaluation_scores"]

        assert "_council" not in scores
        assert "_composite" in scores

    def test_evaluate_with_council(self):
        """Council enabled — _council key present in scores."""
        graph = self._make_graph(council_enabled=True)
        state = {"current_output": "Click here to try again."}

        result = graph._node_evaluate(state)
        scores = result["evaluation_scores"]

        assert "_council" in scores
        council = scores["_council"]
        assert council["consensus_composite"] == 0.85
        assert council["confidence"] == 0.9
        assert council["quorum_met"] is True
        assert "model-a" in council["participating_models"]

    def test_council_property_lazy_load(self):
        """Council evaluator is None when disabled."""
        graph = self._make_graph(council_enabled=False)

        # Force property evaluation
        with patch("runtime.council_config.CouncilConfig.from_config") as mock_load:
            mock_load.return_value = CouncilConfig(enabled=False)
            evaluator = graph.council_evaluator

        assert evaluator is None

    def test_feedback_includes_council_info(self):
        """Feedback builder includes council data when present."""
        graph = self._make_graph(council_enabled=False)
        scores = {
            "readability": {"flesch_reading_ease": 80.0},
            "linter": {"issues": []},
            "_composite": 85,
            "_council": {
                "consensus_composite": 0.85,
                "confidence": 0.9,
                "quorum_met": True,
                "participating_models": ["model-a", "model-b"],
            },
        }
        feedback = graph._build_feedback(scores)

        assert "Council consensus score" in feedback
        assert "0.85" in feedback
        assert "model-a" in feedback

    def test_feedback_without_council(self):
        """Feedback builder works fine without council data."""
        graph = self._make_graph(council_enabled=False)
        scores = {
            "readability": {"flesch_reading_ease": 80.0},
            "linter": {"issues": []},
            "_composite": 85,
        }
        feedback = graph._build_feedback(scores)

        assert "Council" not in feedback
        assert "Composite quality score" in feedback


# ---------------------------------------------------------------------------
# CLI commands
# ---------------------------------------------------------------------------

class TestCLICouncilCommands:
    def test_council_status(self):
        from click.testing import CliRunner
        from runtime.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["council", "status"])
        assert result.exit_code == 0
        assert "Council Configuration" in result.output
        assert "Enabled" in result.output

    def test_council_enable(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        from runtime.cli import main

        # Work in tmp_path so we don't modify the real config
        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "quality_thresholds.yaml").write_text(
            "global:\n  composite_score: 75\n"
        )

        runner = CliRunner()
        result = runner.invoke(main, ["council", "enable"])
        assert result.exit_code == 0
        assert "enabled" in result.output.lower()

    def test_council_disable(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        from runtime.cli import main

        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "quality_thresholds.yaml").write_text(
            "council:\n  enabled: true\n"
        )

        runner = CliRunner()
        result = runner.invoke(main, ["council", "disable"])
        assert result.exit_code == 0
        assert "disabled" in result.output.lower()

    def test_council_configure(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        from runtime.cli import main

        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "quality_thresholds.yaml").write_text(
            "council:\n  enabled: true\n  trigger_conditions:\n    - manual\n"
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["council", "configure", "--min-models", "3", "--consensus-method", "mean"],
        )
        assert result.exit_code == 0
        assert "min_models = 3" in result.output
        assert "consensus_method = mean" in result.output

    def test_council_configure_add_trigger(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        from runtime.cli import main

        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "quality_thresholds.yaml").write_text(
            "council:\n  trigger_conditions:\n    - manual\n"
        )

        runner = CliRunner()
        result = runner.invoke(
            main, ["council", "configure", "--add-trigger", "always"]
        )
        assert result.exit_code == 0
        assert "added trigger: always" in result.output

    def test_council_configure_no_changes(self, tmp_path, monkeypatch):
        from click.testing import CliRunner
        from runtime.cli import main

        monkeypatch.chdir(tmp_path)
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        (config_dir / "quality_thresholds.yaml").write_text("council: {}\n")

        runner = CliRunner()
        result = runner.invoke(main, ["council", "configure"])
        assert result.exit_code == 0
        assert "No changes" in result.output


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_existing_evaluate_unchanged_when_council_disabled(self):
        """Node evaluate produces same output structure when council is off."""
        from runtime.agent import Agent, AgentInput
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter, ScoreReadability

        agent = Agent(
            name="Test", description="test",
            inputs=[AgentInput(name="content", type="string", required=True)],
            available_tools=["run_linter", "score_readability"],
            system_prompt="Test",
            source_file="test.md",
        )
        router = MagicMock()
        memory = MagicMock()
        memory.get_context_for_agent.return_value = ""

        graph = ContentDesignGraph(
            agent=agent,
            tools=[RunLinter(), ScoreReadability()],
            model_router=router,
            memory=memory,
            model="test-model",
        )

        state = {"current_output": "This is a simple test message."}
        result = graph._node_evaluate(state)

        assert "evaluation_scores" in result
        assert "_composite" in result["evaluation_scores"]
        assert "_council" not in result["evaluation_scores"]

    def test_initial_state_unchanged(self):
        from runtime.langgraph_agent import _initial_state

        state = _initial_state(
            agent_name="test",
            user_message="hello",
            system_message="system",
            tools_available=["run_linter"],
        )
        assert "evaluation_scores" in state
        assert state["evaluation_scores"] == {}

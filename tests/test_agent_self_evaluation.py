"""Tests for the agent self-evaluation loop.

Covers evaluation profiles, quality config, evaluation history,
composite scoring, tool assignments, and backward compatibility.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.agent import Agent, AgentInput
from runtime.evaluation_profiles import (
    EVALUATION_PROFILES,
    get_composite_threshold,
    get_evaluation_profile,
    get_weights,
)
from runtime.evaluation_history import EvaluationHistory
from runtime.model_providers import ProviderResponse
from runtime.quality_config import QualityConfig
from runtime.tools.base import ToolResult


# ---------------------------------------------------------------------------
# All agents have tools
# ---------------------------------------------------------------------------

class TestAllAgentsHaveTools:
    def test_all_19_agents_have_tools(self):
        """Every agent definition must have at least one tool."""
        from runtime.loader import load_agents_from_directory
        agents = load_agents_from_directory(Path("content-design"))

        # Exclude the template
        real_agents = [a for a in agents if a.slug != "agent-template"]
        assert len(real_agents) >= 18  # 19 including brand-voice-archaeologist, minus template

        for agent in real_agents:
            assert len(agent.available_tools) > 0, (
                f"Agent '{agent.name}' ({agent.slug}) has no tools defined"
            )

    def test_tool_assignments_valid(self):
        """All tools assigned to agents must exist in the registry."""
        from runtime.loader import load_agents_from_directory
        from runtime.tools.registry import build_default_registry

        registry = build_default_registry()
        agents = load_agents_from_directory(Path("content-design"))

        for agent in agents:
            for tool_name in agent.available_tools:
                assert tool_name in registry, (
                    f"Agent '{agent.name}' references unknown tool '{tool_name}'"
                )


# ---------------------------------------------------------------------------
# Evaluation profiles
# ---------------------------------------------------------------------------

class TestEvaluationProfiles:
    def test_all_agent_types_have_profiles(self):
        """Every agent that has tools should have a profile (or use default)."""
        from runtime.loader import load_agents_from_directory
        agents = load_agents_from_directory(Path("content-design"))

        for agent in agents:
            if agent.available_tools:
                profile = get_evaluation_profile(agent.slug)
                assert "weights" in profile
                assert "thresholds" in profile

    def test_default_profile_exists(self):
        assert "default" in EVALUATION_PROFILES
        default = EVALUATION_PROFILES["default"]
        assert "weights" in default
        assert "thresholds" in default

    def test_get_evaluation_profile_known(self):
        profile = get_evaluation_profile("cta-optimization-specialist")
        assert profile["weights"]["linter"] == 0.4
        assert profile["thresholds"]["composite_score"] == 80

    def test_get_evaluation_profile_unknown_uses_default(self):
        profile = get_evaluation_profile("nonexistent-agent")
        assert profile == EVALUATION_PROFILES["default"]

    def test_weights_sum_to_one(self):
        """All weight sets should sum to approximately 1.0."""
        for agent_type, profile in EVALUATION_PROFILES.items():
            weights = profile["weights"]
            total = sum(weights.values())
            assert abs(total - 1.0) < 0.01, (
                f"Weights for '{agent_type}' sum to {total}, not 1.0"
            )

    def test_get_composite_threshold(self):
        assert get_composite_threshold("accessibility-content-auditor") == 85
        assert get_composite_threshold("default") == 70

    def test_get_weights(self):
        weights = get_weights("tone-evaluation-agent")
        assert weights["voice"] == 0.8
        assert weights["readability"] == 0.2


# ---------------------------------------------------------------------------
# Quality config
# ---------------------------------------------------------------------------

class TestQualityConfig:
    def test_no_config_file(self, tmp_path):
        config = QualityConfig(config_path=tmp_path / "nonexistent.yaml")
        # Falls through to evaluation profile default
        threshold = config.get_threshold("cta-optimization-specialist", "composite_score")
        assert threshold == 80

    def test_user_override(self, tmp_path):
        config_file = tmp_path / "quality.yaml"
        config_file.write_text(
            "cta-optimization-specialist:\n"
            "  composite_score: 95\n",
            encoding="utf-8",
        )
        config = QualityConfig(config_path=config_file)
        assert config.get_threshold("cta-optimization-specialist", "composite_score") == 95

    def test_global_override(self, tmp_path):
        config_file = tmp_path / "quality.yaml"
        config_file.write_text(
            "global:\n"
            "  composite_score: 80\n",
            encoding="utf-8",
        )
        config = QualityConfig(config_path=config_file)
        # Global applies to agents not explicitly listed
        assert config.get_threshold("unknown-agent", "composite_score") == 80

    def test_agent_overrides_global(self, tmp_path):
        config_file = tmp_path / "quality.yaml"
        config_file.write_text(
            "global:\n"
            "  composite_score: 80\n"
            "cta-optimization-specialist:\n"
            "  composite_score: 95\n",
            encoding="utf-8",
        )
        config = QualityConfig(config_path=config_file)
        assert config.get_threshold("cta-optimization-specialist", "composite_score") == 95

    def test_get_all_thresholds(self, tmp_path):
        config_file = tmp_path / "quality.yaml"
        config_file.write_text(
            "global:\n"
            "  readability_min: 50\n",
            encoding="utf-8",
        )
        config = QualityConfig(config_path=config_file)
        thresholds = config.get_all_thresholds("cta-optimization-specialist")
        # Global override should be applied
        assert thresholds["readability_min"] == 50
        # Agent-specific from profile still present
        assert "composite_score" in thresholds

    def test_corrupt_yaml(self, tmp_path):
        config_file = tmp_path / "quality.yaml"
        config_file.write_text(":: not valid yaml [[", encoding="utf-8")
        config = QualityConfig(config_path=config_file)
        # Should fall through to profile defaults
        assert config.get_threshold("default", "composite_score") == 70


# ---------------------------------------------------------------------------
# Evaluation history
# ---------------------------------------------------------------------------

class TestEvaluationHistory:
    def test_record_and_retrieve(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        history.record(
            agent_slug="test-agent",
            scores={"readability": {"flesch_reading_ease": 70}},
            composite_score=75.0,
            passed=True,
        )
        assert history.count() == 1
        assert history.storage_path.exists()

    def test_multiple_records(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        for i in range(5):
            history.record(
                agent_slug="test-agent",
                scores={"readability": {"flesch_reading_ease": 60 + i}},
                composite_score=70 + i,
                passed=True,
            )
        assert history.count() == 5

    def test_get_trends(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        for i in range(3):
            history.record(
                agent_slug="test-agent",
                scores={"readability": 60 + i * 10},
                composite_score=70,
                passed=True,
            )
        trends = history.get_trends("test-agent", "readability")
        assert len(trends) == 3
        assert trends == [60, 70, 80]

    def test_get_pass_rate(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        history.record("a", {}, 80, True)
        history.record("a", {}, 60, False)
        history.record("a", {}, 75, True)
        history.record("b", {}, 50, False)  # Different agent

        rate = history.get_pass_rate("a")
        assert abs(rate - 2 / 3) < 0.01

    def test_pass_rate_no_entries(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        assert history.get_pass_rate("nonexistent") == 0.0

    def test_max_entries_trimmed(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        for i in range(1050):
            history.history.append({
                "timestamp": time.time(),
                "agent_slug": "test",
                "scores": {},
                "composite_score": 70,
                "passed": True,
            })
        history._save()

        # Reload
        history2 = EvaluationHistory(project_dir=tmp_path)
        assert history2.count() <= 1000

    def test_clear(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        history.record("test", {}, 70, True)
        assert history.count() == 1
        removed = history.clear()
        assert removed == 1
        assert history.count() == 0

    def test_load_nonexistent(self, tmp_path):
        history = EvaluationHistory(project_dir=tmp_path)
        assert history.count() == 0

    def test_corrupt_json(self, tmp_path):
        path = tmp_path / ".cd-agency" / "evaluation_history.json"
        path.parent.mkdir(parents=True)
        path.write_text("not json", encoding="utf-8")
        history = EvaluationHistory(project_dir=tmp_path)
        assert history.count() == 0


# ---------------------------------------------------------------------------
# Composite score calculation
# ---------------------------------------------------------------------------

class TestCompositeScoreCalculation:
    def _make_graph(self, agent_slug="test-agent"):
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter, ScoreReadability, CheckAccessibility

        agent = Agent(
            name="Test Agent",
            description="Test",
            source_file=f"{agent_slug}.md",
        )
        tools = [RunLinter(), ScoreReadability(), CheckAccessibility()]
        mock_router = MagicMock()
        return ContentDesignGraph(
            agent=agent,
            tools=tools,
            model_router=mock_router,
            memory=None,
            model="test-model",
        )

    def test_composite_all_perfect(self):
        graph = self._make_graph()
        scores = {
            "readability": {"flesch_reading_ease": 90.0},
            "linter": {"issues_found": 0, "issues": []},
            "accessibility": {"issues": []},
        }
        composite = graph._calculate_composite_score(scores)
        assert composite > 80

    def test_composite_poor_readability(self):
        graph = self._make_graph()
        scores = {
            "readability": {"flesch_reading_ease": 20.0},
            "linter": {"issues_found": 0, "issues": []},
        }
        composite = graph._calculate_composite_score(scores)
        # Readability is low, should pull composite down
        assert composite < 60

    def test_composite_many_lint_issues(self):
        graph = self._make_graph()
        scores = {
            "readability": {"flesch_reading_ease": 80.0},
            "linter": {"issues_found": 10, "issues": [{}] * 10},
        }
        composite = graph._calculate_composite_score(scores)
        # 10 issues = linter score of 0, should pull down composite
        assert composite < 60

    def test_composite_with_voice(self):
        graph = self._make_graph()
        scores = {
            "readability": {"flesch_reading_ease": 70.0},
            "voice": {"score": 9.0},
        }
        composite = graph._calculate_composite_score(scores)
        assert composite > 70

    def test_composite_empty_scores(self):
        graph = self._make_graph()
        composite = graph._calculate_composite_score({})
        assert composite == 0.0

    def test_composite_uses_agent_weights(self):
        """Different agents should weight metrics differently."""
        graph_a11y = self._make_graph("accessibility-content-auditor")
        graph_cta = self._make_graph("cta-optimization-specialist")

        scores = {
            "readability": {"flesch_reading_ease": 60.0},
            "linter": {"issues_found": 0, "issues": []},
            "accessibility": {"issues": [{"rule": "x"}] * 3},  # 3 issues
        }

        score_a11y = graph_a11y._calculate_composite_score(scores)
        score_cta = graph_cta._calculate_composite_score(scores)

        # a11y agent weights accessibility at 0.7 — poor a11y hurts more
        # cta agent doesn't even weight accessibility
        assert score_a11y < score_cta


# ---------------------------------------------------------------------------
# Enhanced should_regenerate
# ---------------------------------------------------------------------------

class TestEnhancedShouldRegenerate:
    def _make_graph(self, agent_slug="test-agent"):
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter, ScoreReadability

        agent = Agent(
            name="Test Agent",
            description="Test",
            source_file=f"{agent_slug}.md",
        )
        tools = [RunLinter(), ScoreReadability()]
        mock_router = MagicMock()
        return ContentDesignGraph(
            agent=agent, tools=tools, model_router=mock_router,
            memory=None, model="test-model",
        )

    def test_regenerate_on_low_composite(self):
        graph = self._make_graph()
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 80.0},
                "linter": {"issues": []},
                "_composite": 30.0,
            },
        }
        assert graph._should_regenerate(state) == "regenerate"

    def test_finalize_on_good_composite(self):
        graph = self._make_graph()
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 80.0},
                "linter": {"issues": []},
                "_composite": 90.0,
            },
        }
        assert graph._should_regenerate(state) == "finalize"

    def test_finalize_on_max_iterations(self):
        graph = self._make_graph()
        state = {
            "iteration_count": 3,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 20.0},
                "_composite": 10.0,
            },
        }
        assert graph._should_regenerate(state) == "finalize"


# ---------------------------------------------------------------------------
# Backward compatibility
# ---------------------------------------------------------------------------

class TestBackwardCompatibility:
    def test_error_message_architect_behavior_unchanged(self):
        """error-message-architect should still use readability + lint checks."""
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter, ScoreReadability, CheckAccessibility
        from runtime.tools.memory_tools import RecallContext, RememberContext
        from runtime.memory import ProjectMemory

        agent = Agent(
            name="Error Message Architect",
            description="Test",
            available_tools=["run_linter", "score_readability", "check_accessibility"],
            system_prompt="You are a test agent.",
            source_file="error-message-architect.md",
        )
        memory = ProjectMemory(project_dir=Path("/tmp/test-eval"))
        tools = [RunLinter(), ScoreReadability(), CheckAccessibility()]
        mock_router = MagicMock()

        graph = ContentDesignGraph(
            agent=agent, tools=tools, model_router=mock_router,
            memory=memory, model="test-model",
        )

        # Good scores → finalize (same as before)
        state = {
            "iteration_count": 1,
            "max_iterations": 3,
            "evaluation_scores": {
                "readability": {"flesch_reading_ease": 80.0},
                "linter": {"issues": []},
                "_composite": 85.0,
            },
        }
        assert graph._should_regenerate(state) == "finalize"

        # Low readability → regenerate (same as before)
        state["evaluation_scores"]["readability"]["flesch_reading_ease"] = 30.0
        state["evaluation_scores"]["_composite"] = 40.0
        assert graph._should_regenerate(state) == "regenerate"

    def test_brand_voice_archaeologist_has_profile(self):
        profile = get_evaluation_profile("brand-voice-archaeologist")
        assert profile["weights"]["voice"] == 0.6


# ---------------------------------------------------------------------------
# Feedback builder includes voice and composite
# ---------------------------------------------------------------------------

class TestFeedbackBuilder:
    def _make_graph(self):
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter, ScoreReadability

        agent = Agent(name="Test", description="Test", source_file="test.md")
        tools = [RunLinter(), ScoreReadability()]
        mock_router = MagicMock()
        return ContentDesignGraph(
            agent=agent, tools=tools, model_router=mock_router,
            memory=None, model="test-model",
        )

    def test_feedback_includes_composite(self):
        graph = self._make_graph()
        scores = {
            "readability": {"flesch_reading_ease": 40.0, "flesch_kincaid_grade": 14},
            "linter": {"issues": []},
            "_composite": 55.0,
        }
        feedback = graph._build_feedback(scores)
        assert "55" in feedback
        assert "Composite" in feedback

    def test_feedback_includes_voice(self):
        graph = self._make_graph()
        scores = {
            "readability": {"flesch_reading_ease": 80.0},
            "linter": {"issues": []},
            "voice": {
                "score": 4,
                "deviations": [{"reason": "Too formal"}],
            },
            "_composite": 60.0,
        }
        feedback = graph._build_feedback(scores)
        assert "Voice" in feedback or "voice" in feedback.lower()


# ---------------------------------------------------------------------------
# Performance limits
# ---------------------------------------------------------------------------

class TestPerformanceLimits:
    def test_max_iterations_default(self):
        from runtime.langgraph_agent import DEFAULT_MAX_ITERATIONS
        assert DEFAULT_MAX_ITERATIONS == 3

    def test_max_iterations_enforced(self):
        from runtime.langgraph_agent import ContentDesignGraph
        from runtime.tools.content_tools import RunLinter

        agent = Agent(name="Test", description="Test", source_file="test.md")
        graph = ContentDesignGraph(
            agent=agent,
            tools=[RunLinter()],
            model_router=MagicMock(),
            memory=None,
            model="test-model",
            max_iterations=2,
        )
        assert graph.max_iterations == 2

        # At max iterations, always finalize regardless of score
        state = {
            "iteration_count": 2,
            "max_iterations": 2,
            "evaluation_scores": {"_composite": 10.0},
        }
        assert graph._should_regenerate(state) == "finalize"

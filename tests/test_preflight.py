"""Tests for the preflight context analysis module."""

import pytest

from runtime.agent import Agent, AgentInput, OutputField
from runtime.preflight import (
    ClarifyingQuestion,
    PreflightResult,
    run_preflight,
    build_assumption_block,
    AGENT_CONTEXT_RULES,
)


@pytest.fixture
def error_agent() -> Agent:
    return Agent(
        name="Error Message Architect",
        description="Writes error messages",
        tags=["error"],
        inputs=[
            AgentInput(name="error_scenario", type="string", required=True, description="The error scenario"),
            AgentInput(name="severity", type="string", required=False, description="Error severity"),
            AgentInput(name="target_audience", type="string", required=False, description="Who sees this"),
            AgentInput(name="brand_guidelines", type="string", required=False, description="Brand tone"),
        ],
        outputs=[
            OutputField(name="error_message", type="string", description="The error message"),
        ],
        system_prompt="You write error messages.",
        source_file="content-design/error-message-architect.md",
    )


@pytest.fixture
def minimal_agent() -> Agent:
    return Agent(
        name="Simple Agent",
        description="A simple agent",
        tags=["test"],
        inputs=[
            AgentInput(name="content", type="string", required=True, description="Content"),
        ],
        outputs=[
            OutputField(name="result", type="string", description="Result"),
        ],
        system_prompt="You are helpful.",
        source_file="content-design/simple-agent.md",
    )


class TestPreflightResult:
    def test_summary_all_provided(self):
        result = PreflightResult(has_enough_context=True)
        assert result.summary() == "All context provided. Ready to generate."

    def test_summary_with_missing_required(self):
        result = PreflightResult(
            has_enough_context=False,
            missing_required=["error_scenario"],
        )
        assert "Missing required" in result.summary()
        assert "error_scenario" in result.summary()

    def test_summary_with_questions(self):
        result = PreflightResult(
            has_enough_context=True,
            questions=[
                ClarifyingQuestion(
                    field_name="severity",
                    question="How severe?",
                    why_it_matters="Determines tone",
                ),
            ],
        )
        assert "1 clarifying question" in result.summary()

    def test_summary_with_assumptions(self):
        result = PreflightResult(
            has_enough_context=True,
            questions=[
                ClarifyingQuestion(
                    field_name="platform",
                    question="What platform?",
                    why_it_matters="Determines conventions",
                ),
            ],
            assumptions=["platform: web"],
        )
        assert "Will assume" in result.summary()


class TestRunPreflight:
    def test_all_fields_provided(self, error_agent: Agent):
        user_input = {
            "error_scenario": "Payment failed",
            "technical_details": "Payment gateway timeout after 30s",
            "severity": "critical",
            "target_audience": "consumer",
            "brand_guidelines": "friendly",
        }
        result = run_preflight(error_agent, user_input)
        assert result.has_enough_context is True
        assert result.missing_required == []
        assert result.questions == []
        assert result.context_score == 1.0

    def test_missing_required_field(self, error_agent: Agent):
        user_input = {"severity": "critical"}
        result = run_preflight(error_agent, user_input)
        assert result.has_enough_context is False
        assert "error_scenario" in result.missing_required

    def test_missing_optional_generates_questions(self, error_agent: Agent):
        user_input = {"error_scenario": "Payment failed"}
        result = run_preflight(error_agent, user_input)
        assert result.has_enough_context is True
        assert len(result.questions) > 0
        field_names = [q.field_name for q in result.questions]
        assert "severity" in field_names

    def test_context_score_calculation(self, error_agent: Agent):
        # 1 of 4 fields provided
        result = run_preflight(error_agent, {"error_scenario": "test"})
        assert result.context_score == pytest.approx(0.25)

        # 2 of 4 fields provided
        result = run_preflight(error_agent, {"error_scenario": "test", "severity": "critical"})
        assert result.context_score == pytest.approx(0.5)

    def test_assumptions_generated_for_missing_optional(self, error_agent: Agent):
        result = run_preflight(error_agent, {"error_scenario": "test"})
        assert len(result.assumptions) > 0
        assumption_text = " ".join(result.assumptions)
        assert "severity" in assumption_text

    def test_no_questions_for_unknown_agent(self, minimal_agent: Agent):
        """Agent without specific rules still gets _default rules."""
        result = run_preflight(minimal_agent, {"content": "test"})
        assert result.has_enough_context is True
        # Should get default target_audience question
        field_names = [q.field_name for q in result.questions]
        assert "target_audience" in field_names

    def test_empty_input(self, error_agent: Agent):
        result = run_preflight(error_agent, {})
        assert result.has_enough_context is False
        assert "error_scenario" in result.missing_required
        assert result.context_score == 0.0

    def test_questions_have_options(self, error_agent: Agent):
        result = run_preflight(error_agent, {"error_scenario": "test"})
        for q in result.questions:
            if q.field_name == "severity":
                assert len(q.suggested_options) > 0
                assert "critical" in q.suggested_options

    def test_no_duplicate_questions(self, error_agent: Agent):
        result = run_preflight(error_agent, {"error_scenario": "test"})
        field_names = [q.field_name for q in result.questions]
        assert len(field_names) == len(set(field_names))


class TestBuildAssumptionBlock:
    def test_empty_assumptions(self):
        result = PreflightResult(has_enough_context=True)
        assert build_assumption_block(result) == ""

    def test_with_assumptions(self):
        result = PreflightResult(
            has_enough_context=True,
            assumptions=["platform: web", "severity: warning level"],
        )
        block = build_assumption_block(result)
        assert "Assumptions" in block
        assert "platform: web" in block
        assert "severity: warning level" in block
        assert "re-run with the correct values" in block


class TestAgentContextRules:
    def test_default_rules_exist(self):
        assert "_default" in AGENT_CONTEXT_RULES
        assert len(AGENT_CONTEXT_RULES["_default"]) > 0

    def test_error_agent_rules_exist(self):
        assert "error-message-architect" in AGENT_CONTEXT_RULES
        rules = AGENT_CONTEXT_RULES["error-message-architect"]
        assert len(rules) >= 2
        fields = [r["field"] for r in rules]
        assert "severity" in fields

    def test_all_rules_have_required_keys(self):
        for slug, rules in AGENT_CONTEXT_RULES.items():
            for rule in rules:
                assert "field" in rule, f"Missing 'field' in {slug}"
                assert "question" in rule, f"Missing 'question' in {slug}"
                assert "why" in rule, f"Missing 'why' in {slug}"

    def test_known_agents_have_rules(self):
        expected_agents = [
            "error-message-architect",
            "microcopy-review-agent",
            "cta-optimization-specialist",
            "notification-content-designer",
            "mobile-ux-writer",
            "onboarding-flow-designer",
            "conversational-ai-designer",
            "empty-state-placeholder-specialist",
            "tone-evaluation-agent",
            "localization-content-strategist",
            "technical-documentation-writer",
            "privacy-legal-content-simplifier",
            "accessibility-content-auditor",
        ]
        for agent_slug in expected_agents:
            assert agent_slug in AGENT_CONTEXT_RULES, f"Missing rules for {agent_slug}"

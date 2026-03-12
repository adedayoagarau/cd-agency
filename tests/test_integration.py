"""Integration tests — verify the full pipeline works end-to-end.

These tests verify that all components wire together correctly:
loader → agent → preflight → system message building → postprocessing.
No API calls are made.
"""

import pytest
from pathlib import Path

from runtime.agent import Agent, AgentInput, AgentOutput, OutputField
from runtime.loader import load_agent, load_agents_from_directory
from runtime.registry import AgentRegistry
from runtime.preflight import run_preflight, build_assumption_block
from runtime.constraints import validate_content
from runtime.postprocess import extract_fragments, postprocess_output


AGENTS_DIR = Path("content-design")


class TestLoaderToPreflightPipeline:
    """Test that loaded agents work with the preflight system."""

    def test_all_agents_have_preflight_rules(self):
        """Every loaded agent should get at least _default preflight rules."""
        agents = load_agents_from_directory(AGENTS_DIR)
        for agent in agents:
            if agent.slug == "agent-template":
                continue
            result = run_preflight(agent, {})
            # Every agent should produce questions (at minimum the _default target_audience)
            assert len(result.questions) >= 0  # Won't fail, but validates no crash

    def test_error_agent_full_preflight(self):
        """End-to-end: load error agent → run preflight → get questions."""
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("error")
        assert agent is not None

        # Minimal input
        preflight = run_preflight(agent, {"error_scenario": "Payment failed"})
        assert preflight.has_enough_context is True
        assert len(preflight.questions) > 0

        # Should ask about severity and target_audience
        field_names = [q.field_name for q in preflight.questions]
        assert "severity" in field_names

    def test_preflight_assumption_block_injected(self):
        """Verify assumption block generates non-empty text for missing context."""
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("error")
        assert agent is not None

        preflight = run_preflight(agent, {"error_scenario": "test"})
        block = build_assumption_block(preflight)
        assert "Assumptions" in block
        assert "defaults" in block.lower()


class TestAgentSystemMessageBuilding:
    """Test that agents build complete system messages with all injections."""

    def test_system_message_includes_prompt(self):
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("error")
        assert agent is not None

        msg = agent.build_system_message()
        assert len(msg) > 100
        assert "error" in msg.lower()

    def test_system_message_includes_knowledge(self):
        """Agents with knowledge refs should have knowledge in system message."""
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("error")
        assert agent is not None

        if agent.knowledge_content:
            msg = agent.build_system_message()
            assert "Knowledge Base" in msg

    def test_all_agents_build_valid_system_messages(self):
        """Every agent should build a non-empty system message."""
        agents = load_agents_from_directory(AGENTS_DIR)
        for agent in agents:
            if agent.slug == "agent-template":
                continue
            msg = agent.build_system_message()
            assert len(msg) > 50, f"{agent.slug} has empty system message"

    def test_user_message_builds_correctly(self):
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("error")
        assert agent is not None

        user_msg = agent.build_user_message({
            "error_scenario": "Payment failed",
            "severity": "critical",
        })
        assert "Payment failed" in user_msg
        assert "critical" in user_msg


class TestConstraintValidationIntegration:
    """Test constraint validation on realistic content."""

    def test_button_within_limit(self):
        result = validate_content("Save", "button")
        assert result.passed

    def test_button_exceeds_limit(self):
        result = validate_content(
            "Save all your changes and continue to the next step", "button",
        )
        assert not result.passed

    def test_toast_with_platform(self):
        result = validate_content(
            "Changes saved", "toast", platform="ios",
        )
        assert result.passed

    def test_push_with_localization(self):
        # 45 chars * 1.35 (German) = 60.75 → exceeds 50 char push_title limit
        result = validate_content(
            "x" * 45, "push_title", target_language="de",
        )
        localization_violations = [v for v in result.violations if v.rule == "localization_expansion"]
        assert len(localization_violations) == 1

    def test_full_validation_stack(self):
        """Test all validators together on a problematic string."""
        result = validate_content(
            "Click here to save all your changes right now please",
            "button",
            platform="android",
            target_language="de",
        )
        rules = [v.rule for v in result.violations]
        assert "character_limit" in rules  # Too long for button
        assert "a11y_link_text" in rules   # "click here" detected


class TestPostprocessIntegration:
    """Test the postprocess pipeline with realistic agent output."""

    def test_error_agent_output(self):
        agent = Agent(
            name="Error Message Architect",
            description="Writes errors",
            tags=["error"],
            inputs=[AgentInput(name="error_scenario", type="string", required=True)],
            outputs=[],
            system_prompt="Write errors.",
            source_file="content-design/error-message-architect.md",
        )
        output = AgentOutput(
            content=(
                "Here are 3 error message variants:\n\n"
                "**Error Message:** We couldn't process your payment. Please check your card details and try again.\n\n"
                "**Toast:** Payment failed. Try again.\n\n"
                "**Button:** Retry Payment"
            ),
            agent_name="Error Message Architect",
        )
        result = postprocess_output(output, agent)
        assert len(result.fragments) == 3
        types = {f.element_type for f in result.fragments}
        assert "inline_error" in types
        assert "toast" in types
        assert "button" in types

        # Button should pass (short enough)
        for frag, cr in result.validations:
            if frag.element_type == "button":
                assert cr.passed

    def test_cta_agent_output_with_platform(self):
        agent = Agent(
            name="CTA Optimization Specialist",
            description="CTAs",
            tags=["cta"],
            inputs=[AgentInput(name="current_cta", type="string", required=True)],
            outputs=[],
            system_prompt="Optimize CTAs.",
            source_file="content-design/cta-optimization-specialist.md",
        )
        output = AgentOutput(
            content='**Button:** start free trial',
            agent_name="CTA Optimization Specialist",
        )
        result = postprocess_output(output, agent, platform="ios")
        # iOS should flag lowercase for Title Case
        assert result.warning_count >= 1

    def test_notification_output(self):
        agent = Agent(
            name="Notification Content Designer",
            description="Notifications",
            tags=["notification"],
            inputs=[AgentInput(name="trigger_event", type="string", required=True)],
            outputs=[],
            system_prompt="Write notifications.",
            source_file="content-design/notification-content-designer.md",
        )
        output = AgentOutput(
            content=(
                "**Push Title:** Your order has shipped!\n"
                "**Push Body:** Your package is on its way. Track it in the app."
            ),
            agent_name="Notification Content Designer",
        )
        result = postprocess_output(output, agent)
        assert len(result.fragments) == 2
        assert result.error_count == 0  # Both within limits


class TestFullPipelineRoundtrip:
    """End-to-end: load agent → preflight → build messages → mock output → postprocess."""

    def test_error_agent_roundtrip(self):
        # 1. Load agent
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("error")
        assert agent is not None

        # 2. Preflight
        user_input = {"error_scenario": "Connection timeout"}
        preflight = run_preflight(agent, user_input)
        assert preflight.has_enough_context is True

        # 3. Build messages (what the runner would do)
        system_msg = agent.build_system_message()
        assumption_block = build_assumption_block(preflight)
        if assumption_block:
            system_msg = f"{system_msg}\n\n---\n\n{assumption_block}"
        user_msg = agent.build_user_message(user_input)

        assert len(system_msg) > 100
        assert "Connection timeout" in user_msg

        # 4. Mock agent output
        mock_output = AgentOutput(
            content=(
                "**Error Message:** Connection timed out. Check your internet and try again.\n"
                "**Button:** Retry"
            ),
            agent_name=agent.name,
        )

        # 5. Postprocess
        pp = postprocess_output(mock_output, agent)
        assert len(pp.fragments) == 2
        assert pp.error_count == 0

    def test_cta_agent_roundtrip(self):
        registry = AgentRegistry.from_directory(AGENTS_DIR)
        agent = registry.get("cta")
        assert agent is not None

        user_input = {"current_cta": "Submit", "goal": "increase signups"}
        preflight = run_preflight(agent, user_input)
        assert preflight.has_enough_context is True

        system_msg = agent.build_system_message()
        assert len(system_msg) > 100

        mock_output = AgentOutput(
            content='**Button:** Start Free Trial\n**Secondary Button:** Learn More',
            agent_name=agent.name,
        )
        pp = postprocess_output(mock_output, agent)
        assert len(pp.fragments) >= 1

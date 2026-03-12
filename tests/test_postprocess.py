"""Tests for the post-processing / auto-validate module."""

import pytest

from runtime.agent import Agent, AgentInput, AgentOutput, OutputField
from runtime.postprocess import (
    ContentFragment,
    PostprocessResult,
    extract_fragments,
    postprocess_output,
    AGENT_DEFAULT_ELEMENTS,
)


@pytest.fixture
def error_agent() -> Agent:
    return Agent(
        name="Error Message Architect",
        description="Writes error messages",
        tags=["error"],
        inputs=[
            AgentInput(name="error_scenario", type="string", required=True, description="The error"),
        ],
        outputs=[OutputField(name="error_message", type="string", description="The message")],
        system_prompt="Write error messages.",
        source_file="content-design/error-message-architect.md",
    )


@pytest.fixture
def cta_agent() -> Agent:
    return Agent(
        name="CTA Optimization Specialist",
        description="Optimizes CTAs",
        tags=["cta"],
        inputs=[
            AgentInput(name="current_cta", type="string", required=True, description="Current CTA"),
        ],
        outputs=[OutputField(name="optimized_cta", type="string", description="CTA")],
        system_prompt="Optimize CTAs.",
        source_file="content-design/cta-optimization-specialist.md",
    )


@pytest.fixture
def generic_agent() -> Agent:
    return Agent(
        name="Generic Agent",
        description="Generic",
        tags=["test"],
        inputs=[],
        outputs=[],
        system_prompt="Be helpful.",
        source_file="content-design/generic-agent.md",
    )


class TestExtractFragments:
    def test_extracts_button(self):
        content = '**Button:** Save Changes\n**Tooltip:** Click to save your work'
        frags = extract_fragments(content)
        assert len(frags) == 2
        assert frags[0].element_type == "button"
        assert frags[0].text == "Save Changes"
        assert frags[1].element_type == "tooltip"
        assert frags[1].text == "Click to save your work"

    def test_extracts_cta_text(self):
        content = '**CTA Text:** Start Free Trial'
        frags = extract_fragments(content)
        assert len(frags) == 1
        assert frags[0].element_type == "button"
        assert frags[0].text == "Start Free Trial"

    def test_extracts_push_notification(self):
        content = '**Push Title:** New message\n**Push Body:** You have a new message from Alice'
        frags = extract_fragments(content)
        types = {f.element_type for f in frags}
        assert "push_title" in types
        assert "push_body" in types

    def test_extracts_toast(self):
        content = '**Toast:** Changes saved successfully'
        frags = extract_fragments(content)
        assert len(frags) == 1
        assert frags[0].element_type == "toast"

    def test_extracts_error_message(self):
        content = '**Error Message:** Unable to connect. Check your internet and try again.'
        frags = extract_fragments(content)
        assert len(frags) == 1
        assert frags[0].element_type == "inline_error"

    def test_extracts_with_quotes(self):
        content = '**Button:** "Save Changes"'
        frags = extract_fragments(content)
        assert frags[0].text == "Save Changes"

    def test_no_fragments_from_plain_text(self, generic_agent: Agent):
        content = "Here are my recommendations for improving your copy."
        frags = extract_fragments(content, generic_agent)
        assert len(frags) == 0

    def test_fallback_to_agent_default_element(self, cta_agent: Agent):
        content = 'I recommend using "Start Free Trial" or "Get Started Now".'
        frags = extract_fragments(content, cta_agent)
        assert len(frags) >= 1
        assert all(f.element_type == "button" for f in frags)

    def test_empty_content(self):
        frags = extract_fragments("")
        assert frags == []

    def test_multiple_labels(self):
        content = (
            "**Primary Button:** Continue\n"
            "**Secondary Button:** Cancel\n"
            "**Headline:** Almost done!\n"
            "**Body:** Review your changes before submitting."
        )
        frags = extract_fragments(content)
        assert len(frags) == 4
        types = [f.element_type for f in frags]
        assert "button" in types
        assert "button_secondary" in types or types.count("button") >= 1
        assert "modal_headline" in types
        assert "modal_body" in types


class TestPostprocessResult:
    def test_no_issues(self):
        from runtime.constraints import ConstraintResult
        frag = ContentFragment(text="Save", element_type="button")
        result = PostprocessResult(
            fragments=[frag],
            validations=[(frag, ConstraintResult())],
        )
        assert result.has_issues is False
        assert result.error_count == 0
        assert result.warning_count == 0
        assert "passed" in result.summary().lower()

    def test_with_errors(self):
        from runtime.constraints import ConstraintResult, ConstraintViolation
        frag = ContentFragment(text="x" * 50, element_type="button")
        cr = ConstraintResult(violations=[
            ConstraintViolation(rule="char_limit", severity="error", message="Too long"),
        ])
        result = PostprocessResult(
            fragments=[frag],
            validations=[(frag, cr)],
        )
        assert result.has_issues is True
        assert result.error_count == 1

    def test_summary_no_fragments(self):
        result = PostprocessResult()
        assert "No content fragments" in result.summary()

    def test_format_report(self):
        from runtime.constraints import ConstraintResult, ConstraintViolation
        frag = ContentFragment(text="Save", element_type="button")
        cr = ConstraintResult(violations=[
            ConstraintViolation(rule="test", severity="warning", message="Close to limit"),
        ])
        result = PostprocessResult(
            fragments=[frag],
            validations=[(frag, cr)],
        )
        report = result.format_report()
        assert "Content Validation Report" in report
        assert "WARN" in report
        assert "Save" in report


class TestPostprocessOutput:
    def test_validates_extracted_fragments(self, error_agent: Agent):
        output = AgentOutput(
            content='**Error Message:** This is a fairly long inline error message that tells the user what went wrong in great detail and exceeds the limit',
            agent_name="Error Message Architect",
        )
        result = postprocess_output(output, error_agent)
        assert len(result.fragments) == 1
        assert result.fragments[0].element_type == "inline_error"
        # The text is >80 chars, should trigger error
        assert result.has_issues is True

    def test_clean_output_passes(self, error_agent: Agent):
        output = AgentOutput(
            content='**Error Message:** Unable to save. Try again.',
            agent_name="Error Message Architect",
        )
        result = postprocess_output(output, error_agent)
        assert len(result.fragments) == 1
        assert result.error_count == 0

    def test_platform_check(self, cta_agent: Agent):
        output = AgentOutput(
            content='**Button:** save changes',
            agent_name="CTA Optimization Specialist",
        )
        result = postprocess_output(output, cta_agent, platform="ios")
        # iOS expects Title Case
        warnings = sum(len(cr.warnings) for _, cr in result.validations)
        assert warnings >= 1

    def test_no_fragments_no_crash(self, generic_agent: Agent):
        output = AgentOutput(
            content="Here is my analysis of your content.",
            agent_name="Generic Agent",
        )
        result = postprocess_output(output, generic_agent)
        assert result.fragments == []
        assert result.validations == []
        assert result.has_issues is False


class TestAgentDefaultElements:
    def test_known_agents_mapped(self):
        assert "error-message-architect" in AGENT_DEFAULT_ELEMENTS
        assert "cta-optimization-specialist" in AGENT_DEFAULT_ELEMENTS
        assert "notification-content-designer" in AGENT_DEFAULT_ELEMENTS
        assert "mobile-ux-writer" in AGENT_DEFAULT_ELEMENTS
        assert "empty-state-placeholder-specialist" in AGENT_DEFAULT_ELEMENTS

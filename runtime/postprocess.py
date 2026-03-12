"""Post-processing for agent output — auto-validates content against constraints.

After an agent generates content, this module extracts text fragments and
validates them against character limits, platform conventions, localization
expansion, and accessibility rules.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from runtime.agent import Agent, AgentOutput
from runtime.constraints import (
    ConstraintResult,
    validate_content,
    ELEMENT_CHAR_LIMITS,
)


# Patterns for extracting labeled content from agent output
# Agents typically output structured content like:
#   **Button:** Save Changes
#   **Headline:** Welcome to your workspace
#   **Toast:** Changes saved successfully
EXTRACT_PATTERNS: list[tuple[str, str]] = [
    # Markdown bold labels → element type
    (r"\*\*(?:CTA|Button|Primary Button|Secondary Button)\s*(?:Text)?[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "button"),
    (r"\*\*(?:Tooltip)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "tooltip"),
    (r"\*\*(?:Toast|Snackbar)\s*(?:Message)?[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "toast"),
    (r"\*\*(?:Push Title|Notification Title)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "push_title"),
    (r"\*\*(?:Push Body|Notification Body)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "push_body"),
    (r"\*\*(?:Headline|Title|Heading)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "modal_headline"),
    (r"\*\*(?:Body|Description|Message)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "modal_body"),
    (r"\*\*(?:Error|Error Message|Inline Error)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "inline_error"),
    (r"\*\*(?:Placeholder)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "placeholder"),
    (r"\*\*(?:Label|Form Label)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "form_label"),
    (r"\*\*(?:Badge|Tag)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "badge"),
    (r"\*\*(?:Empty State Headline)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "empty_state_headline"),
    (r"\*\*(?:Empty State Body)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "empty_state_body"),
    (r"\*\*(?:Email Subject)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "email_subject"),
    (r"\*\*(?:Banner)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "banner"),
    (r"\*\*(?:Nav Label|Navigation)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "nav_label"),
    (r"\*\*(?:Tab)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "tab_label"),
    (r"\*\*(?:Breadcrumb)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "breadcrumb"),
    (r"\*\*(?:SMS)\s*[:\s]*\*\*\s*[\"']?(.+?)[\"']?\s*$", "sms"),
]

# Map agent slugs to the element types they typically produce
AGENT_DEFAULT_ELEMENTS: dict[str, str] = {
    "error-message-architect": "inline_error",
    "cta-optimization-specialist": "button",
    "notification-content-designer": "push_body",
    "mobile-ux-writer": "button",
    "empty-state-placeholder-specialist": "empty_state_body",
}


@dataclass
class ContentFragment:
    """A piece of content extracted from agent output."""

    text: str
    element_type: str
    source_label: str = ""


@dataclass
class PostprocessResult:
    """Result of post-processing agent output."""

    fragments: list[ContentFragment] = field(default_factory=list)
    validations: list[tuple[ContentFragment, ConstraintResult]] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return any(not r.passed for _, r in self.validations)

    @property
    def error_count(self) -> int:
        return sum(len(r.errors) for _, r in self.validations)

    @property
    def warning_count(self) -> int:
        return sum(len(r.warnings) for _, r in self.validations)

    def summary(self) -> str:
        if not self.validations:
            return "No content fragments detected for validation."
        total = len(self.validations)
        errs = self.error_count
        warns = self.warning_count
        if errs == 0 and warns == 0:
            return f"All {total} content fragment(s) passed validation."
        parts = []
        if errs:
            parts.append(f"{errs} error(s)")
        if warns:
            parts.append(f"{warns} warning(s)")
        return f"Validated {total} fragment(s): {', '.join(parts)}"

    def format_report(self) -> str:
        """Format a human-readable validation report."""
        if not self.validations:
            return ""
        lines = ["## Content Validation Report\n"]
        for frag, result in self.validations:
            status = "PASS" if result.passed and not result.warnings else "WARN" if result.passed else "FAIL"
            lines.append(f"**{frag.element_type}** ({len(frag.text)} chars): [{status}]")
            lines.append(f"  Text: \"{frag.text[:80]}{'...' if len(frag.text) > 80 else ''}\"")
            for v in result.violations:
                severity_tag = v.severity.upper()
                lines.append(f"  [{severity_tag}] {v.message}")
            lines.append("")
        lines.append(self.summary())
        return "\n".join(lines)


def extract_fragments(content: str, agent: Agent | None = None) -> list[ContentFragment]:
    """Extract labeled content fragments from agent output.

    Scans for markdown-bold labeled sections like **Button:** Save Changes
    and maps them to UI element types for validation.
    """
    fragments: list[ContentFragment] = []

    for pattern, element_type in EXTRACT_PATTERNS:
        for match in re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE):
            text = match.group(1).strip()
            if text:
                fragments.append(ContentFragment(
                    text=text,
                    element_type=element_type,
                    source_label=match.group(0).strip(),
                ))

    # If no labeled fragments found, try using agent's default element type
    if not fragments and agent:
        default_element = AGENT_DEFAULT_ELEMENTS.get(agent.slug)
        if default_element:
            # Extract quoted strings as potential content fragments
            quoted = re.findall(r'["\u201c](.+?)["\u201d]', content)
            for q in quoted[:5]:  # Limit to first 5 quoted strings
                q = q.strip()
                if 2 <= len(q) <= 200:
                    fragments.append(ContentFragment(
                        text=q,
                        element_type=default_element,
                        source_label="(extracted from quoted text)",
                    ))

    return fragments


def postprocess_output(
    output: AgentOutput,
    agent: Agent,
    *,
    platform: str | None = None,
    target_language: str | None = None,
) -> PostprocessResult:
    """Run constraint validation on agent output.

    Extracts content fragments from the agent's response and validates
    each against character limits, platform conventions, and accessibility.

    Args:
        output: The agent's output.
        agent: The agent that produced the output.
        platform: Target platform for platform-specific checks.
        target_language: Target language for localization checks.

    Returns:
        PostprocessResult with extracted fragments and their validations.
    """
    result = PostprocessResult()

    fragments = extract_fragments(output.content, agent)
    result.fragments = fragments

    for frag in fragments:
        constraint_result = validate_content(
            frag.text,
            frag.element_type,
            platform=platform,
            target_language=target_language,
        )
        result.validations.append((frag, constraint_result))

    return result

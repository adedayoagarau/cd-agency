"""Multi-turn interaction support for agents.

Provides a preflight analysis that identifies missing context
and generates clarifying questions, plus a multi-turn conversation runner.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from runtime.agent import Agent, AgentInput


@dataclass
class ClarifyingQuestion:
    """A question the agent should ask before generating output."""

    field_name: str
    question: str
    why_it_matters: str
    suggested_options: list[str] = field(default_factory=list)
    priority: str = "high"  # high, medium, low


@dataclass
class PreflightResult:
    """Result of a preflight context analysis."""

    has_enough_context: bool
    missing_required: list[str] = field(default_factory=list)
    missing_recommended: list[str] = field(default_factory=list)
    questions: list[ClarifyingQuestion] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    context_score: float = 0.0  # 0-1, how much context we have

    def summary(self) -> str:
        """Human-readable summary of the preflight analysis."""
        if self.has_enough_context and not self.questions:
            return "All context provided. Ready to generate."

        parts = []
        if self.missing_required:
            parts.append(f"Missing required: {', '.join(self.missing_required)}")
        if self.questions:
            parts.append(f"{len(self.questions)} clarifying question(s)")
        if self.assumptions:
            parts.append(f"Will assume: {'; '.join(self.assumptions)}")

        return " | ".join(parts) if parts else "Ready to generate."


# Mapping of agent slugs to recommended optional fields and their questions.
# If a user omits these fields, the agent will surface questions.
AGENT_CONTEXT_RULES: dict[str, list[dict[str, Any]]] = {
    "_default": [
        {
            "field": "target_audience",
            "question": "Who is the user seeing this content?",
            "why": "A technical user gets very different content than a general consumer.",
            "options": ["Non-technical consumer", "Developer/technical user", "Enterprise admin", "Mixed audience"],
            "priority": "high",
        },
    ],
    "error-message-architect": [
        {
            "field": "technical_details",
            "question": "What actually went wrong technically?",
            "why": "Without knowing the real error condition, any specific replacement is just a guess. A timeout, a validation failure, and a permission error need completely different messages.",
            "options": ["Server/API error (5xx, timeout)", "Validation/input error", "Permission/auth error", "Connectivity issue"],
            "priority": "high",
        },
        {
            "field": "severity",
            "question": "How severe is this error?",
            "why": "Critical errors (data at risk, can't proceed) need urgent, direct language. Warnings can be calmer.",
            "options": ["critical", "warning", "info"],
            "priority": "high",
        },
        {
            "field": "target_audience",
            "question": "Who sees this error message?",
            "why": "A developer gets 'API rate limit exceeded (429)'. A consumer gets 'You're sending requests too fast.'",
            "options": ["Non-technical consumer", "Developer", "Enterprise admin"],
            "priority": "high",
        },
        {
            "field": "brand_guidelines",
            "question": "What's your brand tone?",
            "why": "Error messages should match your brand — playful (Slack), professional (Stripe), or minimal (Apple).",
            "options": ["Playful and friendly", "Professional and calm", "Minimal and direct"],
            "priority": "medium",
        },
    ],
    "microcopy-review-agent": [
        {
            "field": "character_limit",
            "question": "What's the character limit for this element?",
            "why": "Buttons need ≤ 25 chars. Tooltips ≤ 120 chars. Without this, I can't validate fit.",
            "options": ["Button (≤ 25)", "Tooltip (≤ 120)", "Toast (≤ 50)", "No limit"],
            "priority": "high",
        },
        {
            "field": "brand_voice",
            "question": "What's the brand voice?",
            "why": "Determines whether suggestions are casual, professional, playful, or minimal.",
            "options": ["Friendly but professional", "Bold and direct", "Playful and casual", "Formal and precise"],
            "priority": "medium",
        },
    ],
    "cta-optimization-specialist": [
        {
            "field": "page_context",
            "question": "Where does this CTA live?",
            "why": "A pricing page CTA is very different from a blog footer CTA. Context drives conversion strategy.",
            "options": ["Pricing page", "Landing page", "Blog post", "Email", "In-app modal"],
            "priority": "high",
        },
        {
            "field": "audience",
            "question": "Who is the target audience?",
            "why": "Their awareness level determines whether the CTA should educate, compare, or convert.",
            "options": ["First-time visitor", "Returning user", "Existing customer (upsell)", "Developer"],
            "priority": "high",
        },
    ],
    "notification-content-designer": [
        {
            "field": "urgency",
            "question": "How urgent is this notification?",
            "why": "Critical notifications need direct language. Low-urgency can be warmer and optional.",
            "options": ["critical", "standard", "low"],
            "priority": "high",
        },
        {
            "field": "user_segment",
            "question": "Who receives this notification?",
            "why": "Free users vs. paying users vs. enterprise admins need different messaging.",
            "options": ["All users", "Free tier", "Paid/Premium", "Enterprise admins"],
            "priority": "medium",
        },
    ],
    "mobile-ux-writer": [
        {
            "field": "platform",
            "question": "iOS, Android, or both?",
            "why": "iOS uses Title Case for buttons, Android uses sentence case. Alert button order is different.",
            "options": ["ios", "android", "cross-platform"],
            "priority": "high",
        },
        {
            "field": "character_limit",
            "question": "What's the character limit?",
            "why": "Push notifications, buttons, and toasts all have different limits.",
            "options": ["Push notification (≤ 120)", "Button (≤ 25)", "Toast (≤ 50)", "Auto-detect from element type"],
            "priority": "high",
        },
    ],
    "onboarding-flow-designer": [
        {
            "field": "target_user",
            "question": "Who is the target user?",
            "why": "A non-technical consumer needs hand-holding. A developer wants to skip to the API key.",
            "options": ["Non-technical consumer", "Small business owner", "Developer", "Enterprise team lead"],
            "priority": "high",
        },
        {
            "field": "platform",
            "question": "What platform?",
            "why": "Mobile onboarding needs shorter text, larger touch targets, and fewer steps.",
            "options": ["web", "mobile", "desktop", "cross-platform"],
            "priority": "high",
        },
    ],
    "conversational-ai-designer": [
        {
            "field": "platform",
            "question": "What platform is this conversation on?",
            "why": "Web chat, Alexa, IVR, and SMS have very different constraints and capabilities.",
            "options": ["Web chat widget", "Voice assistant (Alexa/Google)", "IVR phone system", "SMS", "WhatsApp"],
            "priority": "high",
        },
        {
            "field": "ai_persona",
            "question": "What personality should the AI have?",
            "why": "The persona determines vocabulary, tone, and conversational style.",
            "options": ["Friendly assistant", "Professional advisor", "Concise helper", "Custom (specify)"],
            "priority": "high",
        },
    ],
    "empty-state-placeholder-specialist": [
        {
            "field": "desired_action",
            "question": "What should the user do from this empty state?",
            "why": "The CTA is the most important part — without it, the empty state is a dead end.",
            "options": ["Create something new", "Adjust filters/search", "Wait (data will appear)", "No action needed"],
            "priority": "high",
        },
        {
            "field": "brand_voice",
            "question": "What tone should the empty state have?",
            "why": "A playful empty state in a banking app feels wrong. Match tone to product domain.",
            "options": ["playful", "professional", "minimal"],
            "priority": "medium",
        },
    ],
    "tone-evaluation-agent": [
        {
            "field": "target_tone",
            "question": "What tone are you aiming for?",
            "why": "Without a target, I can only describe the current tone — I can't tell you how to improve it.",
            "options": ["Warm and encouraging", "Professional and confident", "Casual and fun", "Minimal and direct"],
            "priority": "high",
        },
        {
            "field": "channel",
            "question": "Where does this content appear?",
            "why": "An error message needs different tone than a marketing email or help article.",
            "options": ["Marketing email", "Error state", "Help article", "Onboarding", "Push notification"],
            "priority": "high",
        },
    ],
    "localization-content-strategist": [
        {
            "field": "target_languages",
            "question": "What languages will this be translated to?",
            "why": "German expands 30%, Japanese contracts. The target language determines character budget.",
            "options": ["German", "French", "Spanish", "Japanese", "Chinese", "Multiple (specify)"],
            "priority": "high",
        },
    ],
    "search-experience-writer": [
        {
            "field": "common_queries",
            "question": "What do users typically search for?",
            "why": "Real search behavior informs placeholder text and autocomplete suggestions.",
            "options": [],
            "priority": "medium",
        },
    ],
    "technical-documentation-writer": [
        {
            "field": "audience",
            "question": "What's the reader's technical level?",
            "why": "A junior developer needs more context and explanation. A senior engineer wants terse reference.",
            "options": ["Junior developer", "Senior backend engineer", "DevOps/SRE", "Non-technical stakeholder"],
            "priority": "high",
        },
        {
            "field": "programming_language",
            "question": "What language should code examples use?",
            "why": "Code examples must be in the reader's language to be immediately useful.",
            "options": ["Python", "JavaScript/TypeScript", "Go", "Java", "Multiple"],
            "priority": "high",
        },
    ],
    "privacy-legal-content-simplifier": [
        {
            "field": "jurisdiction",
            "question": "What legal jurisdiction applies?",
            "why": "GDPR, CCPA, and PIPEDA have different requirements. This changes what MUST be included.",
            "options": ["GDPR (EU)", "CCPA (California)", "PIPEDA (Canada)", "Multiple/Global"],
            "priority": "high",
        },
    ],
    "accessibility-content-auditor": [
        {
            "field": "wcag_level",
            "question": "What WCAG compliance level?",
            "why": "Level A is minimum, AA is standard (most regulations), AAA is enhanced.",
            "options": ["A (minimum)", "AA (standard)", "AAA (enhanced)"],
            "priority": "medium",
        },
    ],
    "information-architect": [
        {
            "field": "scope",
            "question": "What scope should the analysis cover?",
            "why": "A single page has a flat entity set. A full product has hierarchies, cross-references, and edge cases. Scope changes the depth of analysis.",
            "options": ["Single page", "User flow", "Feature area", "Full product"],
            "priority": "high",
        },
        {
            "field": "existing_taxonomy",
            "question": "Is there an existing naming convention or taxonomy?",
            "why": "If the product already uses established terms, the analysis should work within or evolve that model rather than replace it.",
            "options": [],
            "priority": "medium",
        },
    ],
}


def run_preflight(agent: Agent, user_input: dict[str, Any]) -> PreflightResult:
    """Analyze user input and identify missing context, generate questions.

    Returns a PreflightResult with missing fields, clarifying questions,
    and assumptions the agent will make if the user proceeds without answering.
    """
    slug = agent.slug
    missing_required = []
    missing_recommended = []
    questions = []
    assumptions = []

    # Check required fields
    for inp in agent.inputs:
        if inp.required and (inp.name not in user_input or not user_input.get(inp.name)):
            missing_required.append(inp.name)

    # Get context rules for this agent
    rules = AGENT_CONTEXT_RULES.get(slug, []) + AGENT_CONTEXT_RULES.get("_default", [])

    # Deduplicate by field name
    seen_fields: set[str] = set()
    deduped_rules: list[dict[str, Any]] = []
    for rule in rules:
        if rule["field"] not in seen_fields:
            seen_fields.add(rule["field"])
            deduped_rules.append(rule)

    for rule in deduped_rules:
        field_name = rule["field"]
        # Skip if already provided
        if field_name in user_input and user_input[field_name]:
            continue

        # Skip if it's a required field (already flagged)
        if field_name in missing_required:
            continue

        missing_recommended.append(field_name)
        questions.append(ClarifyingQuestion(
            field_name=field_name,
            question=rule["question"],
            why_it_matters=rule["why"],
            suggested_options=rule.get("options", []),
            priority=rule.get("priority", "medium"),
        ))

    # Generate assumptions for missing optional fields
    default_assumptions = {
        "target_audience": "general consumer audience",
        "platform": "web (responsive)",
        "brand_voice": "professional but approachable",
        "character_limit": "standard limits for the UI element type",
        "severity": "warning level (not critical)",
        "wcag_level": "WCAG 2.1 Level AA",
        "channel": "in-app",
        "urgency": "standard urgency",
        "jurisdiction": "GDPR (EU) as the strictest common standard",
    }

    for q in questions:
        if q.field_name in default_assumptions:
            assumptions.append(
                f"{q.field_name}: {default_assumptions[q.field_name]}"
            )

    # Score context completeness
    total_fields = len(agent.inputs)
    provided_fields = sum(
        1 for inp in agent.inputs
        if inp.name in user_input and user_input[inp.name]
    )
    context_score = provided_fields / max(total_fields, 1)

    has_enough = len(missing_required) == 0

    return PreflightResult(
        has_enough_context=has_enough,
        missing_required=missing_required,
        missing_recommended=missing_recommended,
        questions=questions,
        assumptions=assumptions,
        context_score=context_score,
    )


def build_assumption_block(preflight: PreflightResult) -> str:
    """Build a text block stating assumptions for injection into the prompt."""
    if not preflight.assumptions:
        return ""

    lines = ["## Assumptions (context not provided — using defaults)\n"]
    for assumption in preflight.assumptions:
        lines.append(f"- {assumption}")
    lines.append(
        "\nIf any of these assumptions are wrong, "
        "re-run with the correct values for better results."
    )
    return "\n".join(lines)

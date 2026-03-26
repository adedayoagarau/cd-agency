"""Content evaluation tools — wrappers around existing scoring modules."""

from __future__ import annotations

import json
from typing import Any

from runtime.tools.base import Tool, ToolResult


class RunLinter(Tool):
    """Run the content linter and return issues found."""

    name = "run_linter"
    description = (
        "Lint UI content for jargon, passive voice, inclusive language, "
        "and content-type-specific rules (CTA, error, button, notification). "
        "Returns a list of lint issues with severity and suggestions."
    )
    parameters = {
        "text": {"type": "string", "description": "The text content to lint"},
        "content_type": {
            "type": "string",
            "description": "Content type: general, cta, error, button, notification, microcopy",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        text = kwargs.get("text", "")
        content_type = kwargs.get("content_type", "general")
        if not text:
            return ToolResult(success=False, error="No text provided")

        from tools.linter import ContentLinter

        linter = ContentLinter()
        results = linter.lint(text, content_type)

        issues = [r.to_dict() for r in results if not r.passed]
        passed = [r.to_dict() for r in results if r.passed]

        return ToolResult(
            success=True,
            data={
                "total_rules": len(results),
                "issues_found": len(issues),
                "passed": len(passed),
                "issues": issues,
                "all_passed": len(issues) == 0,
            },
        )


class ScoreReadability(Tool):
    """Score text readability using Flesch-Kincaid metrics."""

    name = "score_readability"
    description = (
        "Calculate readability scores for text content. Returns Flesch Reading Ease "
        "(0-100, higher = easier), Flesch-Kincaid Grade Level, word count, sentence "
        "count, and complexity index. Target: ease >= 60, grade <= 8 for general UI."
    )
    parameters = {
        "text": {"type": "string", "description": "The text content to score"},
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        text = kwargs.get("text", "")
        if not text:
            return ToolResult(success=False, error="No text provided")

        from tools.scoring import ReadabilityScorer

        scorer = ReadabilityScorer()
        result = scorer.score(text)

        return ToolResult(
            success=True,
            data=result.to_dict(),
        )


class CheckAccessibility(Tool):
    """Check text for WCAG accessibility issues."""

    name = "check_accessibility"
    description = (
        "Check content for WCAG text-level accessibility issues including: "
        "reading level, sentence complexity, ALL CAPS, emoji overuse, "
        "'click here' anti-patterns, and missing alt text. Returns issues "
        "with WCAG criterion references and severity levels."
    )
    parameters = {
        "text": {"type": "string", "description": "The text content to check"},
        "target_grade": {
            "type": "number",
            "description": "Target reading grade level (default: 8.0)",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        text = kwargs.get("text", "")
        target_grade = kwargs.get("target_grade", 8.0)
        if not text:
            return ToolResult(success=False, error="No text provided")

        from tools.a11y_checker import A11yChecker

        checker = A11yChecker(target_grade=target_grade)
        result = checker.check(text)

        return ToolResult(
            success=True,
            data=result.to_dict(),
        )


class CheckVoiceConsistency(Tool):
    """Check content against brand voice guidelines (rule-based, no LLM)."""

    name = "check_voice_consistency"
    description = (
        "Check content against a brand voice profile using rule-based heuristics. "
        "Returns a 1-10 score, deviations from voice guidelines, and strengths. "
        "Does not require an API call."
    )
    parameters = {
        "text": {"type": "string", "description": "The text content to check"},
        "tone_descriptors": {
            "type": "string",
            "description": "Comma-separated tone words, e.g. 'friendly, professional, warm'",
            "optional": True,
        },
        "do_list": {
            "type": "string",
            "description": "Comma-separated list of voice guidelines to follow",
            "optional": True,
        },
        "dont_list": {
            "type": "string",
            "description": "Comma-separated list of voice anti-patterns to avoid",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        text = kwargs.get("text", "")
        if not text:
            return ToolResult(success=False, error="No text provided")

        from tools.voice_checker import VoiceChecker, VoiceProfile

        tone = kwargs.get("tone_descriptors", "")
        do_str = kwargs.get("do_list", "")
        dont_str = kwargs.get("dont_list", "")

        profile = VoiceProfile(
            name="custom",
            tone_descriptors=[t.strip() for t in tone.split(",") if t.strip()] if tone else [],
            do_list=[d.strip() for d in do_str.split(",") if d.strip()] if do_str else [],
            dont_list=[d.strip() for d in dont_str.split(",") if d.strip()] if dont_str else [],
        )

        checker = VoiceChecker()
        result = checker.check_without_llm(text, profile)

        return ToolResult(
            success=True,
            data=result.to_dict(),
        )

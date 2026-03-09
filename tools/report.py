"""Scoring report generation — terminal, JSON, and Markdown outputs."""

import json
from dataclasses import dataclass, field
from enum import Enum

from tools.scoring import ReadabilityResult
from tools.linter import LintResult, LintSeverity
from tools.a11y_checker import A11yResult, A11ySeverity
from tools.voice_checker import VoiceResult


class ReportFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    MARKDOWN = "markdown"


@dataclass
class ScoringReport:
    """Consolidated scoring report across all tools."""

    text: str
    readability: ReadabilityResult | None = None
    lint_results: list[LintResult] = field(default_factory=list)
    a11y_result: A11yResult | None = None
    voice_result: VoiceResult | None = None

    # Comparison mode
    before_readability: ReadabilityResult | None = None

    @property
    def overall_pass(self) -> bool:
        """Overall pass/fail based on all checks."""
        if self.lint_results:
            errors = [r for r in self.lint_results if not r.passed and r.severity == LintSeverity.ERROR]
            if errors:
                return False
        if self.a11y_result and not self.a11y_result.passed:
            return False
        if self.voice_result and self.voice_result.score < 5:
            return False
        return True

    def render(self, fmt: ReportFormat = ReportFormat.TEXT) -> str:
        """Render the report in the specified format."""
        if fmt == ReportFormat.JSON:
            return self._render_json()
        elif fmt == ReportFormat.MARKDOWN:
            return self._render_markdown()
        else:
            return self._render_text()

    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        result = {"overall_pass": self.overall_pass}
        if self.readability:
            result["readability"] = self.readability.to_dict()
        if self.lint_results:
            result["lint"] = {
                "passed": all(r.passed for r in self.lint_results if r.severity == LintSeverity.ERROR),
                "results": [r.to_dict() for r in self.lint_results],
            }
        if self.a11y_result:
            result["accessibility"] = self.a11y_result.to_dict()
        if self.voice_result:
            result["voice"] = self.voice_result.to_dict()
        if self.before_readability:
            result["comparison"] = {
                "before": self.before_readability.to_dict(),
                "after": self.readability.to_dict() if self.readability else None,
            }
        return result

    def _render_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def _render_text(self) -> str:
        """Render a plain-text terminal report."""
        lines = []
        lines.append("=" * 60)
        lines.append("  CONTENT SCORING REPORT")
        lines.append("=" * 60)
        status = "PASS" if self.overall_pass else "FAIL"
        lines.append(f"  Overall: {status}")
        lines.append("")

        if self.readability:
            lines.append("--- Readability ---")
            r = self.readability
            lines.append(f"  Words: {r.word_count}  |  Sentences: {r.sentence_count}")
            lines.append(f"  Flesch Reading Ease: {r.flesch_reading_ease} ({r.ease_label})")
            lines.append(f"  Flesch-Kincaid Grade: {r.flesch_kincaid_grade} ({r.grade_label})")
            lines.append(f"  Avg sentence length: {r.avg_sentence_length} words")
            lines.append(f"  Complexity index: {r.complexity_index}")
            lines.append(f"  Reading time: {r.reading_time_seconds}s")
            lines.append("")

        if self.before_readability and self.readability:
            lines.append("--- Before/After Comparison ---")
            b = self.before_readability
            a = self.readability
            grade_change = round(a.flesch_kincaid_grade - b.flesch_kincaid_grade, 1)
            ease_change = round(a.flesch_reading_ease - b.flesch_reading_ease, 1)
            word_change = a.word_count - b.word_count
            sign = lambda x: f"+{x}" if x > 0 else str(x)
            lines.append(f"  Grade level: {b.flesch_kincaid_grade} -> {a.flesch_kincaid_grade} ({sign(grade_change)})")
            lines.append(f"  Reading ease: {b.flesch_reading_ease} -> {a.flesch_reading_ease} ({sign(ease_change)})")
            lines.append(f"  Word count: {b.word_count} -> {a.word_count} ({sign(word_change)})")
            lines.append("")

        if self.lint_results:
            lines.append("--- Content Lint ---")
            for r in self.lint_results:
                icon = "PASS" if r.passed else "FAIL"
                lines.append(f"  [{icon}] {r.rule}: {r.message}")
                if not r.passed and r.suggestion:
                    lines.append(f"         -> {r.suggestion}")
                if not r.passed and r.matches:
                    lines.append(f"         Found: {', '.join(r.matches[:5])}")
            lines.append("")

        if self.a11y_result:
            lines.append("--- Accessibility ---")
            lines.append(f"  Status: {self.a11y_result.label}")
            lines.append(f"  Reading grade: {self.a11y_result.reading_grade} (target: {self.a11y_result.target_grade})")
            for issue in self.a11y_result.issues:
                lines.append(f"  [{issue.severity.value.upper()}] {issue.rule}: {issue.message}")
                if issue.suggestion:
                    lines.append(f"         -> {issue.suggestion}")
                lines.append(f"         WCAG: {issue.wcag_criterion}")
            lines.append("")

        if self.voice_result:
            lines.append("--- Brand Voice ---")
            lines.append(f"  Score: {self.voice_result.score}/10 ({self.voice_result.label})")
            lines.append(f"  Summary: {self.voice_result.summary}")
            if self.voice_result.deviations:
                lines.append("  Deviations:")
                for d in self.voice_result.deviations:
                    lines.append(f"    - \"{d.phrase}\": {d.reason}")
                    if d.suggestion:
                        lines.append(f"      -> {d.suggestion}")
            if self.voice_result.strengths:
                lines.append("  Strengths:")
                for s in self.voice_result.strengths:
                    lines.append(f"    + {s}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def _render_markdown(self) -> str:
        """Render a Markdown report."""
        lines = []
        lines.append("# Content Scoring Report")
        lines.append("")
        status = "Pass" if self.overall_pass else "**FAIL**"
        lines.append(f"**Overall: {status}**")
        lines.append("")

        if self.readability:
            lines.append("## Readability")
            lines.append("")
            r = self.readability
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Word count | {r.word_count} |")
            lines.append(f"| Sentence count | {r.sentence_count} |")
            lines.append(f"| Flesch Reading Ease | {r.flesch_reading_ease} ({r.ease_label}) |")
            lines.append(f"| Flesch-Kincaid Grade | {r.flesch_kincaid_grade} ({r.grade_label}) |")
            lines.append(f"| Avg sentence length | {r.avg_sentence_length} words |")
            lines.append(f"| Complexity index | {r.complexity_index} |")
            lines.append(f"| Reading time | {r.reading_time_seconds}s |")
            lines.append("")

        if self.before_readability and self.readability:
            lines.append("## Before/After Comparison")
            lines.append("")
            b = self.before_readability
            a = self.readability
            lines.append("| Metric | Before | After | Change |")
            lines.append("|--------|--------|-------|--------|")
            grade_diff = round(a.flesch_kincaid_grade - b.flesch_kincaid_grade, 1)
            ease_diff = round(a.flesch_reading_ease - b.flesch_reading_ease, 1)
            word_diff = a.word_count - b.word_count
            lines.append(f"| Grade level | {b.flesch_kincaid_grade} | {a.flesch_kincaid_grade} | {grade_diff:+} |")
            lines.append(f"| Reading ease | {b.flesch_reading_ease} | {a.flesch_reading_ease} | {ease_diff:+} |")
            lines.append(f"| Word count | {b.word_count} | {a.word_count} | {word_diff:+} |")
            lines.append("")

        if self.lint_results:
            lines.append("## Content Lint")
            lines.append("")
            lines.append("| Rule | Status | Message |")
            lines.append("|------|--------|---------|")
            for r in self.lint_results:
                icon = "Pass" if r.passed else "**FAIL**"
                lines.append(f"| {r.rule} | {icon} | {r.message} |")
            lines.append("")
            failures = [r for r in self.lint_results if not r.passed]
            if failures:
                lines.append("### Suggestions")
                lines.append("")
                for r in failures:
                    if r.suggestion:
                        lines.append(f"- **{r.rule}**: {r.suggestion}")
                lines.append("")

        if self.a11y_result:
            lines.append("## Accessibility")
            lines.append("")
            lines.append(f"**Status**: {self.a11y_result.label}")
            lines.append("")
            if self.a11y_result.issues:
                lines.append("| Severity | Rule | Issue | WCAG |")
                lines.append("|----------|------|-------|------|")
                for issue in self.a11y_result.issues:
                    lines.append(f"| {issue.severity.value} | {issue.rule} | {issue.message} | {issue.wcag_criterion} |")
                lines.append("")

        if self.voice_result:
            lines.append("## Brand Voice")
            lines.append("")
            lines.append(f"**Score**: {self.voice_result.score}/10 ({self.voice_result.label})")
            lines.append(f"\n{self.voice_result.summary}")
            lines.append("")

        return "\n".join(lines)

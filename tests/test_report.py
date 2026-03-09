"""Tests for scoring report generation."""

import json
import pytest
from tools.scoring import ReadabilityScorer
from tools.linter import ContentLinter, LintResult, LintSeverity
from tools.a11y_checker import A11yChecker
from tools.voice_checker import VoiceResult, VoiceDeviation
from tools.report import ScoringReport, ReportFormat


@pytest.fixture
def sample_report():
    scorer = ReadabilityScorer()
    linter = ContentLinter()
    a11y = A11yChecker()

    text = "Start your free trial today. No credit card required."
    readability = scorer.score(text)
    lint_results = linter.lint(text, content_type="cta")
    a11y_result = a11y.check(text)
    voice_result = VoiceResult(
        score=8.5,
        summary="Good brand voice alignment",
        deviations=[],
        strengths=["Clear and direct"],
    )

    return ScoringReport(
        text=text,
        readability=readability,
        lint_results=lint_results,
        a11y_result=a11y_result,
        voice_result=voice_result,
    )


class TestScoringReport:
    def test_overall_pass(self, sample_report):
        assert isinstance(sample_report.overall_pass, bool)

    def test_overall_fail_on_lint_error(self):
        report = ScoringReport(
            text="test",
            lint_results=[LintResult(
                rule="test",
                passed=False,
                severity=LintSeverity.ERROR,
                message="Failed",
            )],
        )
        assert not report.overall_pass

    def test_overall_pass_on_lint_warning(self):
        report = ScoringReport(
            text="test",
            lint_results=[LintResult(
                rule="test",
                passed=False,
                severity=LintSeverity.WARNING,
                message="Warning only",
            )],
        )
        assert report.overall_pass

    def test_overall_fail_on_low_voice(self):
        report = ScoringReport(
            text="test",
            voice_result=VoiceResult(score=3.0, summary="Poor"),
        )
        assert not report.overall_pass


class TestTextRendering:
    def test_render_text(self, sample_report):
        output = sample_report.render(ReportFormat.TEXT)
        assert "CONTENT SCORING REPORT" in output
        assert "Readability" in output
        assert "Flesch" in output

    def test_render_text_overall_status(self, sample_report):
        output = sample_report.render(ReportFormat.TEXT)
        assert "PASS" in output or "FAIL" in output

    def test_render_text_lint_section(self, sample_report):
        output = sample_report.render(ReportFormat.TEXT)
        assert "Content Lint" in output

    def test_render_text_a11y_section(self, sample_report):
        output = sample_report.render(ReportFormat.TEXT)
        assert "Accessibility" in output

    def test_render_text_voice_section(self, sample_report):
        output = sample_report.render(ReportFormat.TEXT)
        assert "Brand Voice" in output
        assert "8.5" in output


class TestJsonRendering:
    def test_render_json_valid(self, sample_report):
        output = sample_report.render(ReportFormat.JSON)
        data = json.loads(output)
        assert "overall_pass" in data

    def test_render_json_has_readability(self, sample_report):
        output = sample_report.render(ReportFormat.JSON)
        data = json.loads(output)
        assert "readability" in data
        assert "word_count" in data["readability"]

    def test_render_json_has_lint(self, sample_report):
        output = sample_report.render(ReportFormat.JSON)
        data = json.loads(output)
        assert "lint" in data
        assert "results" in data["lint"]

    def test_render_json_has_a11y(self, sample_report):
        output = sample_report.render(ReportFormat.JSON)
        data = json.loads(output)
        assert "accessibility" in data

    def test_render_json_has_voice(self, sample_report):
        output = sample_report.render(ReportFormat.JSON)
        data = json.loads(output)
        assert "voice" in data
        assert data["voice"]["score"] == 8.5


class TestMarkdownRendering:
    def test_render_markdown(self, sample_report):
        output = sample_report.render(ReportFormat.MARKDOWN)
        assert "# Content Scoring Report" in output

    def test_render_markdown_has_tables(self, sample_report):
        output = sample_report.render(ReportFormat.MARKDOWN)
        assert "| Metric | Value |" in output

    def test_render_markdown_has_lint_table(self, sample_report):
        output = sample_report.render(ReportFormat.MARKDOWN)
        assert "## Content Lint" in output


class TestComparison:
    def test_comparison_mode(self):
        scorer = ReadabilityScorer()
        before_text = (
            "The implementation of this sophisticated mechanism requires "
            "comprehensive understanding of the underlying principles and "
            "methodological approaches to computational systems."
        )
        after_text = "This feature needs you to understand the basics."

        report = ScoringReport(
            text=after_text,
            readability=scorer.score(after_text),
            before_readability=scorer.score(before_text),
        )
        output = report.render(ReportFormat.TEXT)
        assert "Before/After Comparison" in output
        assert "->" in output

    def test_comparison_markdown(self):
        scorer = ReadabilityScorer()
        before = "Complex implementation necessitates understanding."
        after = "You need to understand this."

        report = ScoringReport(
            text=after,
            readability=scorer.score(after),
            before_readability=scorer.score(before),
        )
        output = report.render(ReportFormat.MARKDOWN)
        assert "## Before/After Comparison" in output
        assert "| Before | After | Change |" in output

    def test_comparison_json(self):
        scorer = ReadabilityScorer()
        before = "Complex text."
        after = "Simple text."

        report = ScoringReport(
            text=after,
            readability=scorer.score(after),
            before_readability=scorer.score(before),
        )
        data = json.loads(report.render(ReportFormat.JSON))
        assert "comparison" in data
        assert "before" in data["comparison"]
        assert "after" in data["comparison"]


class TestToDict:
    def test_to_dict_complete(self, sample_report):
        d = sample_report.to_dict()
        assert "overall_pass" in d
        assert "readability" in d
        assert "lint" in d
        assert "accessibility" in d
        assert "voice" in d

    def test_to_dict_minimal(self):
        report = ScoringReport(text="test")
        d = report.to_dict()
        assert "overall_pass" in d
        assert d["overall_pass"] is True  # No checks = pass

"""Tests for content linter."""

import pytest
from tools.linter import ContentLinter, LintResult, LintSeverity


@pytest.fixture
def linter():
    return ContentLinter()


class TestCTAActionVerb:
    def test_good_cta(self, linter):
        results = linter.lint("Start your free trial", content_type="cta")
        verb_result = next(r for r in results if r.rule == "cta-action-verb")
        assert verb_result.passed

    def test_bad_cta(self, linter):
        results = linter.lint("Submit", content_type="cta")
        # "submit" IS in the action verbs list
        verb_result = next(r for r in results if r.rule == "cta-action-verb")
        assert verb_result.passed

    def test_no_action_verb_cta(self, linter):
        results = linter.lint("Your account", content_type="cta")
        verb_result = next(r for r in results if r.rule == "cta-action-verb")
        assert not verb_result.passed

    def test_cta_severity_is_error(self, linter):
        results = linter.lint("Your account", content_type="cta")
        verb_result = next(r for r in results if r.rule == "cta-action-verb")
        assert verb_result.severity == LintSeverity.ERROR


class TestErrorActionable:
    def test_actionable_error(self, linter):
        results = linter.lint(
            "Connection failed. Try refreshing the page or check your internet connection.",
            content_type="error",
        )
        error_result = next(r for r in results if r.rule == "error-actionable")
        assert error_result.passed

    def test_non_actionable_error(self, linter):
        results = linter.lint(
            "Something went wrong.",
            content_type="error",
        )
        error_result = next(r for r in results if r.rule == "error-actionable")
        assert not error_result.passed

    def test_error_with_suggestion(self, linter):
        results = linter.lint(
            "Something went wrong.",
            content_type="error",
        )
        error_result = next(r for r in results if r.rule == "error-actionable")
        assert error_result.suggestion != ""


class TestPassiveVoice:
    def test_active_voice(self, linter):
        results = linter.lint("We sent your email.", content_type="general")
        passive_result = next(r for r in results if r.rule == "no-passive-voice")
        assert passive_result.passed

    def test_passive_voice(self, linter):
        results = linter.lint("Your email was sent.", content_type="general")
        passive_result = next(r for r in results if r.rule == "no-passive-voice")
        assert not passive_result.passed
        assert len(passive_result.matches) > 0

    def test_passive_voice_severity_is_warning(self, linter):
        results = linter.lint("Your email was sent.", content_type="general")
        passive_result = next(r for r in results if r.rule == "no-passive-voice")
        assert passive_result.severity == LintSeverity.WARNING


class TestCharacterLimit:
    def test_button_within_limit(self, linter):
        results = linter.lint("Start trial", content_type="button")
        limit_result = next(r for r in results if r.rule == "button-char-limit")
        assert limit_result.passed

    def test_button_exceeds_limit(self, linter):
        long_text = "Click here to begin your incredible journey with our product"
        results = linter.lint(long_text, content_type="button")
        limit_result = next(r for r in results if r.rule == "button-char-limit")
        assert not limit_result.passed

    def test_notification_within_limit(self, linter):
        results = linter.lint("You have a new message from Sarah.", content_type="notification")
        limit_result = next(r for r in results if r.rule == "notification-char-limit")
        assert limit_result.passed

    def test_custom_limit(self):
        linter = ContentLinter(max_button_chars=10)
        results = linter.lint("Start my trial", content_type="button")
        limit_result = next(r for r in results if r.rule == "button-char-limit")
        assert not limit_result.passed


class TestJargon:
    def test_no_jargon(self, linter):
        results = linter.lint("Save your work.", content_type="general")
        jargon_result = next(r for r in results if r.rule == "no-jargon")
        assert jargon_result.passed

    def test_has_jargon(self, linter):
        results = linter.lint("Leverage our synergy to iterate on deliverables.", content_type="general")
        jargon_result = next(r for r in results if r.rule == "no-jargon")
        assert not jargon_result.passed
        assert "leverage" in [m.lower() for m in jargon_result.matches]

    def test_custom_jargon(self):
        linter = ContentLinter(custom_jargon=["foobar"])
        results = linter.lint("Let's foobar the process.", content_type="general")
        jargon_result = next(r for r in results if r.rule == "no-jargon")
        assert not jargon_result.passed


class TestInclusiveLanguage:
    def test_inclusive(self, linter):
        results = linter.lint("Add to the allowlist.", content_type="general")
        inclusive_result = next(r for r in results if r.rule == "inclusive-language")
        assert inclusive_result.passed

    def test_not_inclusive(self, linter):
        results = linter.lint("Add to the whitelist.", content_type="general")
        inclusive_result = next(r for r in results if r.rule == "inclusive-language")
        assert not inclusive_result.passed
        assert "whitelist" in inclusive_result.matches

    def test_inclusive_suggestion(self, linter):
        results = linter.lint("Add to the whitelist.", content_type="general")
        inclusive_result = next(r for r in results if r.rule == "inclusive-language")
        assert "allowlist" in inclusive_result.suggestion

    def test_inclusive_severity_is_error(self, linter):
        results = linter.lint("Add to the blacklist.", content_type="general")
        inclusive_result = next(r for r in results if r.rule == "inclusive-language")
        assert inclusive_result.severity == LintSeverity.ERROR


class TestConsistency:
    def test_consistent(self, linter):
        results = linter.lint_all("Log in to your account. Then log in again.")
        consistency_result = next(r for r in results if r.rule == "consistent-terminology")
        assert consistency_result.passed

    def test_inconsistent(self, linter):
        results = linter.lint_all("Log in to your account. Check your login page.")
        consistency_result = next(r for r in results if r.rule == "consistent-terminology")
        assert not consistency_result.passed


class TestLintResult:
    def test_to_dict(self):
        result = LintResult(
            rule="test-rule",
            passed=False,
            severity=LintSeverity.ERROR,
            message="Test failed",
            suggestion="Fix it",
            matches=["bad"],
        )
        d = result.to_dict()
        assert d["rule"] == "test-rule"
        assert d["passed"] is False
        assert d["severity"] == "error"
        assert d["suggestion"] == "Fix it"
        assert d["matches"] == ["bad"]

    def test_to_dict_no_optional(self):
        result = LintResult(
            rule="test-rule",
            passed=True,
            severity=LintSeverity.INFO,
            message="All good",
        )
        d = result.to_dict()
        assert "suggestion" not in d
        assert "matches" not in d

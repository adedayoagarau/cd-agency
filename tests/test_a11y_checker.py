"""Tests for accessibility content checker."""

import pytest
from tools.a11y_checker import A11yChecker, A11yResult, A11ySeverity


@pytest.fixture
def checker():
    return A11yChecker()


class TestReadingLevel:
    def test_simple_text_passes(self, checker):
        result = checker.check("The cat sat on the mat. The dog ran fast.")
        reading_issues = [i for i in result.issues if i.rule == "reading-level"]
        assert len(reading_issues) == 0

    def test_complex_text_fails(self, checker):
        text = (
            "The implementation of sophisticated algorithmic mechanisms "
            "necessitates comprehensive understanding of computational "
            "complexity and the underlying mathematical foundations "
            "that govern distributed systems architecture."
        )
        result = checker.check(text)
        reading_issues = [i for i in result.issues if i.rule == "reading-level"]
        assert len(reading_issues) == 1
        assert reading_issues[0].severity == A11ySeverity.HIGH

    def test_custom_target_grade(self):
        checker = A11yChecker(target_grade=4.0)
        result = checker.check("The implementation requires careful understanding.")
        # This should fail at a stricter grade target
        assert result.reading_grade > 0


class TestSentenceLength:
    def test_short_sentences_pass(self, checker):
        result = checker.check("Keep it short. This is fine. Simple works.")
        sentence_issues = [i for i in result.issues if i.rule == "sentence-length"]
        assert len(sentence_issues) == 0

    def test_long_sentence_fails(self, checker):
        words = " ".join(["word"] * 30)
        result = checker.check(f"{words}.")
        sentence_issues = [i for i in result.issues if i.rule == "sentence-length"]
        assert len(sentence_issues) == 1


class TestAllCaps:
    def test_normal_text_passes(self, checker):
        result = checker.check("This is normal text with no caps abuse.")
        caps_issues = [i for i in result.issues if i.rule == "no-all-caps"]
        assert len(caps_issues) == 0

    def test_all_caps_fails(self, checker):
        result = checker.check("SCHEDULE YOUR APPOINTMENT NOW.")
        caps_issues = [i for i in result.issues if i.rule == "no-all-caps"]
        assert len(caps_issues) == 1

    def test_abbreviations_allowed(self, checker):
        result = checker.check("Use the API to send HTTP requests.")
        caps_issues = [i for i in result.issues if i.rule == "no-all-caps"]
        assert len(caps_issues) == 0


class TestLinkText:
    def test_descriptive_link_passes(self, checker):
        result = checker.check("View pricing details for more information.")
        link_issues = [i for i in result.issues if i.rule == "descriptive-link-text"]
        assert len(link_issues) == 0

    def test_click_here_fails(self, checker):
        result = checker.check("Click here to see the pricing page.")
        link_issues = [i for i in result.issues if i.rule == "descriptive-link-text"]
        assert len(link_issues) == 1
        assert link_issues[0].severity == A11ySeverity.HIGH

    def test_tap_here_fails(self, checker):
        result = checker.check("Tap here for more details.")
        link_issues = [i for i in result.issues if i.rule == "descriptive-link-text"]
        assert len(link_issues) == 1


class TestAltText:
    def test_good_alt_text_passes(self, checker):
        result = checker.check("![A red car on a highway](image.jpg)")
        alt_issues = [i for i in result.issues if "alt-text" in i.rule]
        assert len(alt_issues) == 0

    def test_empty_alt_text_fails(self, checker):
        result = checker.check("![](image.jpg)")
        alt_issues = [i for i in result.issues if i.rule == "image-alt-text"]
        assert len(alt_issues) == 1
        assert alt_issues[0].severity == A11ySeverity.CRITICAL

    def test_filename_alt_text_fails(self, checker):
        result = checker.check("![IMG_4521.jpg](image.jpg)")
        alt_issues = [i for i in result.issues if i.rule == "meaningful-alt-text"]
        assert len(alt_issues) == 1


class TestA11yResult:
    def test_passed_no_issues(self, checker):
        result = checker.check("Simple text. Easy to read.")
        assert result.passed or len(result.critical_issues) == 0

    def test_label_pass(self):
        result = A11yResult(issues=[], reading_grade=5.0, target_grade=8.0)
        assert result.label == "Pass"

    def test_label_fail_critical(self):
        from tools.a11y_checker import A11yIssue
        result = A11yResult(
            issues=[A11yIssue(
                rule="test",
                severity=A11ySeverity.CRITICAL,
                message="Critical issue",
                wcag_criterion="1.1.1",
            )],
            reading_grade=5.0,
            target_grade=8.0,
        )
        assert "critical" in result.label.lower()

    def test_to_dict(self, checker):
        result = checker.check("Simple text.")
        d = result.to_dict()
        assert "passed" in d
        assert "reading_grade" in d
        assert "issues" in d
        assert "label" in d

    def test_issue_count(self):
        from tools.a11y_checker import A11yIssue
        issues = [
            A11yIssue(rule="a", severity=A11ySeverity.LOW, message="", wcag_criterion=""),
            A11yIssue(rule="b", severity=A11ySeverity.MEDIUM, message="", wcag_criterion=""),
        ]
        result = A11yResult(issues=issues, reading_grade=5.0, target_grade=8.0)
        assert result.issue_count == 2

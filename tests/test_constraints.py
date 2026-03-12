"""Tests for the constraint validation module."""

import pytest

from runtime.constraints import (
    ConstraintViolation,
    ConstraintResult,
    validate_character_limit,
    validate_localization,
    validate_platform_conventions,
    validate_accessibility,
    validate_content,
    get_element_limit,
    list_element_types,
    ELEMENT_CHAR_LIMITS,
    EXPANSION_FACTORS,
    PLATFORM_CONVENTIONS,
)


class TestConstraintResult:
    def test_passed_with_no_violations(self):
        result = ConstraintResult()
        assert result.passed is True
        assert result.errors == []
        assert result.warnings == []

    def test_passed_with_only_warnings(self):
        result = ConstraintResult(violations=[
            ConstraintViolation(rule="test", severity="warning", message="warn"),
        ])
        assert result.passed is True

    def test_failed_with_errors(self):
        result = ConstraintResult(violations=[
            ConstraintViolation(rule="test", severity="error", message="err"),
        ])
        assert result.passed is False

    def test_errors_property(self):
        result = ConstraintResult(violations=[
            ConstraintViolation(rule="a", severity="error", message="err1"),
            ConstraintViolation(rule="b", severity="warning", message="warn"),
            ConstraintViolation(rule="c", severity="error", message="err2"),
        ])
        assert len(result.errors) == 2
        assert len(result.warnings) == 1

    def test_summary_no_violations(self):
        result = ConstraintResult()
        assert result.summary() == "All constraints passed."

    def test_summary_with_violations(self):
        result = ConstraintResult(violations=[
            ConstraintViolation(rule="a", severity="error", message="err"),
            ConstraintViolation(rule="b", severity="warning", message="warn"),
        ])
        summary = result.summary()
        assert "1 error" in summary
        assert "1 warning" in summary


class TestValidateCharacterLimit:
    def test_within_limit(self):
        result = validate_character_limit("Save", "button")
        assert result.passed is True
        assert len(result.violations) == 0

    def test_exceeds_limit(self):
        long_text = "This is a very long button text that exceeds limits"
        result = validate_character_limit(long_text, "button")
        assert result.passed is False
        assert result.violations[0].rule == "character_limit"
        assert result.violations[0].severity == "error"

    def test_near_limit_warning(self):
        # Button max is 25. 23 chars = 92% = should warn
        text = "x" * 23
        result = validate_character_limit(text, "button")
        assert result.passed is True
        assert len(result.violations) == 1
        assert result.violations[0].severity == "warning"

    def test_custom_limit(self):
        result = validate_character_limit("Hello world", "button", custom_limit=5)
        assert result.passed is False

    def test_unknown_element_no_limit(self):
        result = validate_character_limit("anything", "unknown_element")
        assert result.passed is True
        assert len(result.violations) == 0

    def test_all_element_types_have_limits(self):
        for element_type in ELEMENT_CHAR_LIMITS:
            limit = get_element_limit(element_type)
            assert limit is not None
            assert limit > 0


class TestValidateLocalization:
    def test_german_expansion(self):
        # Button max is 25. "Save changes" is 12 chars. German factor is 1.35 → 16 chars. OK.
        result = validate_localization("Save changes", "button", "de")
        assert len(result.violations) == 0

    def test_german_expansion_exceeds(self):
        # 20 chars * 1.35 = 27, exceeds button max of 25
        text = "x" * 20
        result = validate_localization(text, "button", "de")
        assert len(result.violations) == 1
        assert "expand" in result.violations[0].message.lower()

    def test_japanese_contraction(self):
        # Japanese factor is 0.80 — text gets shorter
        text = "x" * 25
        result = validate_localization(text, "button", "ja")
        # 25 * 0.80 = 20, within 25 limit
        assert len(result.violations) == 0

    def test_unknown_language(self):
        result = validate_localization("test", "button", "xx")
        assert len(result.violations) == 0

    def test_all_languages_have_factors(self):
        expected = ["de", "fr", "es", "it", "pt", "ja", "zh", "ko"]
        for lang in expected:
            assert lang in EXPANSION_FACTORS


class TestValidatePlatformConventions:
    def test_ios_title_case(self):
        result = validate_platform_conventions("save changes", "button", "ios")
        violations = [v for v in result.violations if v.rule == "platform_case"]
        assert len(violations) == 1
        assert "Title Case" in violations[0].message

    def test_ios_title_case_passes(self):
        result = validate_platform_conventions("Save Changes", "button", "ios")
        violations = [v for v in result.violations if v.rule == "platform_case"]
        assert len(violations) == 0

    def test_android_sentence_case(self):
        result = validate_platform_conventions("Save Changes", "button", "android")
        violations = [v for v in result.violations if v.rule == "platform_case"]
        assert len(violations) == 1
        assert "sentence case" in violations[0].message

    def test_push_title_limit_android(self):
        long_title = "x" * 45  # Android push title max is 40
        result = validate_platform_conventions(long_title, "push_title", "android")
        violations = [v for v in result.violations if v.rule == "platform_push_title_limit"]
        assert len(violations) == 1

    def test_interaction_verb_web(self):
        result = validate_platform_conventions("Tap here to continue", "button", "web")
        violations = [v for v in result.violations if v.rule == "platform_interaction_verb"]
        assert len(violations) == 1
        assert "Click" in violations[0].message

    def test_unknown_platform(self):
        result = validate_platform_conventions("test", "button", "unknown")
        assert len(result.violations) == 0

    def test_all_platforms_exist(self):
        assert "ios" in PLATFORM_CONVENTIONS
        assert "android" in PLATFORM_CONVENTIONS
        assert "web" in PLATFORM_CONVENTIONS


class TestValidateAccessibility:
    def test_click_here_error(self):
        result = validate_accessibility("Click here for details", "button")
        violations = [v for v in result.violations if v.rule == "a11y_link_text"]
        assert len(violations) == 1
        assert violations[0].severity == "error"

    def test_learn_more_warning(self):
        result = validate_accessibility("Learn more", "button")
        violations = [v for v in result.violations if v.rule == "a11y_vague_link"]
        assert len(violations) == 1
        assert violations[0].severity == "warning"

    def test_learn_more_with_topic_ok(self):
        result = validate_accessibility("Learn more about pricing", "button")
        violations = [v for v in result.violations if v.rule == "a11y_vague_link"]
        assert len(violations) == 0

    def test_all_caps_warning(self):
        result = validate_accessibility("CLICK HERE NOW PLEASE", "button")
        violations = [v for v in result.violations if v.rule == "a11y_all_caps"]
        assert len(violations) == 1

    def test_placeholder_info(self):
        result = validate_accessibility("Enter email", "placeholder")
        violations = [v for v in result.violations if v.rule == "a11y_placeholder_warning"]
        assert len(violations) == 1
        assert violations[0].severity == "info"

    def test_clean_text_passes(self):
        result = validate_accessibility("Save changes", "button")
        assert len(result.violations) == 0


class TestValidateContent:
    def test_combines_all_checks(self):
        result = validate_content(
            "Click here to save your changes right now please",
            "button",
            platform="ios",
            target_language="de",
        )
        # Should have character limit error + a11y error + possibly platform/localization
        assert result.passed is False

    def test_clean_content_passes(self):
        result = validate_content("Save", "button")
        assert result.passed is True

    def test_platform_only(self):
        result = validate_content("Save Changes", "button", platform="android")
        violations = [v for v in result.violations if v.rule == "platform_case"]
        assert len(violations) == 1

    def test_language_only(self):
        text = "x" * 20
        result = validate_content(text, "button", target_language="de")
        violations = [v for v in result.violations if v.rule == "localization_expansion"]
        assert len(violations) == 1


class TestHelpers:
    def test_get_element_limit(self):
        assert get_element_limit("button") == 25
        assert get_element_limit("tooltip") == 120
        assert get_element_limit("nonexistent") is None

    def test_list_element_types(self):
        elements = list_element_types()
        assert len(elements) == len(ELEMENT_CHAR_LIMITS)
        for e in elements:
            assert "type" in e
            assert "max_chars" in e
            assert "label" in e

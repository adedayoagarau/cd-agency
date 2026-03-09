"""Tests for brand voice consistency checker."""

import pytest
from tools.voice_checker import VoiceChecker, VoiceProfile, VoiceResult, VoiceDeviation


@pytest.fixture
def profile():
    return VoiceProfile(
        name="Friendly Tech",
        tone_descriptors=["warm", "professional", "clear"],
        do_list=[
            "Use simple, direct language",
            "Address users as 'you'",
            "Be encouraging",
        ],
        dont_list=[
            "Use jargon or buzzwords",
            "Be condescending or patronizing",
            "Use passive voice",
        ],
        sample_content=[
            "You're all set! Your project is ready.",
            "Need help? We're here for you.",
        ],
    )


class TestVoiceProfile:
    def test_from_dict(self):
        data = {
            "name": "Test Brand",
            "tone_descriptors": ["fun", "bold"],
            "do": ["Be direct"],
            "dont": ["Be boring"],
        }
        profile = VoiceProfile.from_dict(data)
        assert profile.name == "Test Brand"
        assert len(profile.tone_descriptors) == 2
        assert len(profile.do_list) == 1
        assert len(profile.dont_list) == 1

    def test_to_prompt(self, profile):
        prompt = profile.to_prompt()
        assert "Friendly Tech" in prompt
        assert "warm" in prompt
        assert "simple" in prompt.lower()
        assert "jargon" in prompt.lower()

    def test_sample_content_in_prompt(self, profile):
        prompt = profile.to_prompt()
        assert "You're all set" in prompt


class TestVoiceResult:
    def test_excellent_label(self):
        result = VoiceResult(score=9.5, summary="Great match")
        assert result.label == "Excellent"

    def test_good_label(self):
        result = VoiceResult(score=7.5, summary="Good match")
        assert result.label == "Good"

    def test_needs_work_label(self):
        result = VoiceResult(score=5.5, summary="Needs work")
        assert result.label == "Needs Work"

    def test_poor_label(self):
        result = VoiceResult(score=3.5, summary="Poor match")
        assert result.label == "Poor"

    def test_off_brand_label(self):
        result = VoiceResult(score=2.0, summary="Off brand")
        assert result.label == "Off-Brand"

    def test_to_dict(self):
        result = VoiceResult(
            score=8.0,
            summary="Good overall",
            deviations=[VoiceDeviation(phrase="leverage", reason="jargon", suggestion="use")],
            strengths=["Direct language"],
        )
        d = result.to_dict()
        assert d["score"] == 8.0
        assert d["label"] == "Good"
        assert len(d["deviations"]) == 1
        assert d["deviations"][0]["phrase"] == "leverage"
        assert len(d["strengths"]) == 1


class TestVoiceCheckerWithoutLLM:
    def test_matching_content(self, profile):
        checker = VoiceChecker()
        text = "You're all set! Your project is ready to go."
        result = checker.check_without_llm(text, profile)
        assert result.score > 5

    def test_violating_content(self, profile):
        checker = VoiceChecker()
        # Text containing words from don't rules: "condescending", "patronizing", "passive"
        text = "Obviously you should know this already. Don't be so passive about your decisions."
        result = checker.check_without_llm(text, profile)
        # Should detect violations from don't rules
        assert len(result.deviations) > 0

    def test_result_summary(self, profile):
        checker = VoiceChecker()
        result = checker.check_without_llm("Simple clear text.", profile)
        assert "voice rules" in result.summary

    def test_score_bounded(self, profile):
        checker = VoiceChecker()
        text = "jargon buzzwords condescending patronizing passive"
        result = checker.check_without_llm(text, profile)
        assert 1.0 <= result.score <= 10.0


class TestVoiceCheckerParseResponse:
    def test_valid_json(self):
        checker = VoiceChecker()
        response = '{"score": 8, "summary": "Good", "deviations": [], "strengths": ["Clear"]}'
        result = checker._parse_response(response)
        assert result.score == 8.0
        assert result.summary == "Good"
        assert len(result.strengths) == 1

    def test_json_in_code_block(self):
        checker = VoiceChecker()
        response = '```json\n{"score": 7, "summary": "OK", "deviations": [], "strengths": []}\n```'
        result = checker._parse_response(response)
        assert result.score == 7.0

    def test_invalid_json(self):
        checker = VoiceChecker()
        result = checker._parse_response("not json at all")
        assert result.score == 5.0  # Default fallback
        assert "Could not parse" in result.summary

    def test_deviations_parsed(self):
        checker = VoiceChecker()
        response = (
            '{"score": 6, "summary": "OK", '
            '"deviations": [{"phrase": "leverage", "reason": "jargon", "suggestion": "use"}], '
            '"strengths": []}'
        )
        result = checker._parse_response(response)
        assert len(result.deviations) == 1
        assert result.deviations[0].phrase == "leverage"

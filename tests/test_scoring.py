"""Tests for readability scoring."""

import pytest
from tools.scoring import ReadabilityScorer, ReadabilityResult


@pytest.fixture
def scorer():
    return ReadabilityScorer()


class TestReadabilityScorer:
    def test_empty_text(self, scorer):
        result = scorer.score("")
        assert result.word_count == 0
        assert result.flesch_reading_ease == 0
        assert result.flesch_kincaid_grade == 0

    def test_simple_sentence(self, scorer):
        result = scorer.score("The cat sat on the mat.")
        assert result.word_count == 6
        assert result.sentence_count == 1
        assert result.avg_sentence_length == 6
        # Simple text should have high reading ease
        assert result.flesch_reading_ease > 70

    def test_complex_text(self, scorer):
        text = (
            "The implementation of sophisticated algorithmic mechanisms "
            "necessitates comprehensive understanding of computational "
            "complexity and mathematical foundations."
        )
        result = scorer.score(text)
        # Complex text should have lower reading ease
        assert result.flesch_reading_ease < 50
        # And higher grade level
        assert result.flesch_kincaid_grade > 10

    def test_multiple_sentences(self, scorer):
        text = "Short sentence. Another short one. And a third."
        result = scorer.score(text)
        assert result.sentence_count == 3
        assert result.min_sentence_length == 2
        assert result.max_sentence_length == 3

    def test_word_count(self, scorer):
        result = scorer.score("One two three four five.")
        assert result.word_count == 5

    def test_character_count(self, scorer):
        text = "Hello world."
        result = scorer.score(text)
        assert result.character_count == len(text)

    def test_syllable_counting(self, scorer):
        # "beautiful" has 3 syllables
        assert scorer._count_syllables("beautiful") >= 3
        # "cat" has 1 syllable
        assert scorer._count_syllables("cat") == 1
        # "understanding" has 4+ syllables
        assert scorer._count_syllables("understanding") >= 4
        # Single letter
        assert scorer._count_syllables("a") == 1

    def test_reading_time(self, scorer):
        # 238 words should take about 60 seconds
        words = " ".join(["word"] * 238) + "."
        result = scorer.score(words)
        assert 55 < result.reading_time_seconds < 65

    def test_complexity_index(self, scorer):
        # Simple text should have low complexity
        simple = "The cat sat on the mat. The dog ran fast."
        result = scorer.score(simple)
        assert result.complexity_index < 0.1

    def test_grade_label(self, scorer):
        result = scorer.score("Go. Run. Stop.")
        assert "Easy" in result.grade_label or "Very Easy" in result.grade_label

    def test_ease_label(self, scorer):
        result = scorer.score("Go. Run. Stop.")
        assert result.ease_label in ("Very Easy", "Easy", "Fairly Easy")

    def test_to_dict(self, scorer):
        result = scorer.score("Simple test sentence.")
        d = result.to_dict()
        assert "word_count" in d
        assert "flesch_reading_ease" in d
        assert "flesch_kincaid_grade" in d
        assert "grade_label" in d
        assert "ease_label" in d

    def test_compare(self, scorer):
        before = (
            "The implementation of this sophisticated mechanism requires "
            "comprehensive understanding of the underlying principles."
        )
        after = "This feature needs you to understand the basics."
        comparison = scorer.compare(before, after)
        assert "before" in comparison
        assert "after" in comparison
        assert "improvements" in comparison
        # After should have lower grade
        assert comparison["improvements"]["grade_change"] < 0
        # After should have higher reading ease
        assert comparison["improvements"]["ease_change"] > 0

    def test_flesch_reading_ease_bounded(self, scorer):
        result = scorer.score("Go.")
        assert 0 <= result.flesch_reading_ease <= 100

    def test_flesch_kincaid_grade_non_negative(self, scorer):
        result = scorer.score("Go.")
        assert result.flesch_kincaid_grade >= 0

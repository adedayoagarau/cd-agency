"""Readability and text quality scoring."""

import re
import math
from dataclasses import dataclass, field


@dataclass
class ReadabilityResult:
    """Results from readability analysis."""

    text: str
    word_count: int
    character_count: int
    sentence_count: int
    syllable_count: int
    avg_sentence_length: float
    max_sentence_length: int
    min_sentence_length: int
    avg_word_length: float
    flesch_reading_ease: float
    flesch_kincaid_grade: float
    complexity_index: float
    reading_time_seconds: float

    @property
    def grade_label(self) -> str:
        """Human-readable grade level label."""
        grade = self.flesch_kincaid_grade
        if grade <= 5:
            return "Very Easy (5th grade)"
        elif grade <= 8:
            return "Easy (6th-8th grade)"
        elif grade <= 12:
            return "Standard (9th-12th grade)"
        elif grade <= 16:
            return "Difficult (college level)"
        else:
            return "Very Difficult (graduate level)"

    @property
    def ease_label(self) -> str:
        """Human-readable reading ease label."""
        score = self.flesch_reading_ease
        if score >= 90:
            return "Very Easy"
        elif score >= 80:
            return "Easy"
        elif score >= 70:
            return "Fairly Easy"
        elif score >= 60:
            return "Standard"
        elif score >= 50:
            return "Fairly Difficult"
        elif score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"

    def to_dict(self) -> dict:
        return {
            "word_count": self.word_count,
            "character_count": self.character_count,
            "sentence_count": self.sentence_count,
            "syllable_count": self.syllable_count,
            "avg_sentence_length": round(self.avg_sentence_length, 1),
            "max_sentence_length": self.max_sentence_length,
            "min_sentence_length": self.min_sentence_length,
            "avg_word_length": round(self.avg_word_length, 1),
            "flesch_reading_ease": round(self.flesch_reading_ease, 1),
            "flesch_kincaid_grade": round(self.flesch_kincaid_grade, 1),
            "complexity_index": round(self.complexity_index, 2),
            "reading_time_seconds": round(self.reading_time_seconds, 1),
            "grade_label": self.grade_label,
            "ease_label": self.ease_label,
        }


class ReadabilityScorer:
    """Calculates readability metrics for text content."""

    # Words per minute for average reader
    WPM = 238

    def score(self, text: str) -> ReadabilityResult:
        """Score text for readability metrics."""
        words = self._get_words(text)
        sentences = self._get_sentences(text)
        word_count = len(words)
        sentence_count = len(sentences)

        if word_count == 0:
            return ReadabilityResult(
                text=text,
                word_count=0,
                character_count=len(text),
                sentence_count=0,
                syllable_count=0,
                avg_sentence_length=0,
                max_sentence_length=0,
                min_sentence_length=0,
                avg_word_length=0,
                flesch_reading_ease=0,
                flesch_kincaid_grade=0,
                complexity_index=0,
                reading_time_seconds=0,
            )

        syllable_count = sum(self._count_syllables(w) for w in words)
        sentence_lengths = [len(self._get_words(s)) for s in sentences]
        sentence_lengths = [l for l in sentence_lengths if l > 0]

        if not sentence_lengths:
            sentence_lengths = [word_count]
            sentence_count = 1

        avg_sentence_length = word_count / sentence_count
        avg_syllables_per_word = syllable_count / word_count

        # Flesch Reading Ease: 206.835 - 1.015(words/sentences) - 84.6(syllables/words)
        flesch_ease = (
            206.835
            - 1.015 * avg_sentence_length
            - 84.6 * avg_syllables_per_word
        )
        flesch_ease = max(0, min(100, flesch_ease))

        # Flesch-Kincaid Grade: 0.39(words/sentences) + 11.8(syllables/words) - 15.59
        fk_grade = (
            0.39 * avg_sentence_length
            + 11.8 * avg_syllables_per_word
            - 15.59
        )
        fk_grade = max(0, fk_grade)

        # Complexity index: ratio of complex words (3+ syllables) to total words
        complex_words = sum(1 for w in words if self._count_syllables(w) >= 3)
        complexity_index = complex_words / word_count if word_count > 0 else 0

        char_count = sum(len(w) for w in words)
        avg_word_length = char_count / word_count

        return ReadabilityResult(
            text=text,
            word_count=word_count,
            character_count=len(text),
            sentence_count=sentence_count,
            syllable_count=syllable_count,
            avg_sentence_length=round(avg_sentence_length, 1),
            max_sentence_length=max(sentence_lengths),
            min_sentence_length=min(sentence_lengths),
            avg_word_length=round(avg_word_length, 1),
            flesch_reading_ease=round(flesch_ease, 1),
            flesch_kincaid_grade=round(fk_grade, 1),
            complexity_index=round(complexity_index, 3),
            reading_time_seconds=round(word_count / self.WPM * 60, 1),
        )

    def compare(self, before: str, after: str) -> dict:
        """Compare readability of before and after text."""
        before_result = self.score(before)
        after_result = self.score(after)
        return {
            "before": before_result.to_dict(),
            "after": after_result.to_dict(),
            "improvements": {
                "word_count_change": after_result.word_count - before_result.word_count,
                "grade_change": round(
                    after_result.flesch_kincaid_grade - before_result.flesch_kincaid_grade, 1
                ),
                "ease_change": round(
                    after_result.flesch_reading_ease - before_result.flesch_reading_ease, 1
                ),
                "complexity_change": round(
                    after_result.complexity_index - before_result.complexity_index, 3
                ),
            },
        }

    def _get_words(self, text: str) -> list[str]:
        """Extract words from text."""
        return re.findall(r"[a-zA-Z']+", text)

    def _get_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Split on sentence-ending punctuation
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word using a heuristic approach."""
        word = word.lower().strip()
        if not word:
            return 0
        if len(word) <= 2:
            return 1

        # Remove trailing silent e
        if word.endswith("e") and not word.endswith("le"):
            word = word[:-1]

        # Count vowel groups
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        return max(1, count)

"""Accessibility text-level compliance checker."""

import re
from dataclasses import dataclass, field
from enum import Enum

from tools.scoring import ReadabilityScorer


class A11ySeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class A11yIssue:
    """A single accessibility issue found in content."""

    rule: str
    severity: A11ySeverity
    message: str
    wcag_criterion: str
    suggestion: str = ""
    matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "wcag_criterion": self.wcag_criterion,
        }
        if self.suggestion:
            d["suggestion"] = self.suggestion
        if self.matches:
            d["matches"] = self.matches
        return d


@dataclass
class A11yResult:
    """Result of accessibility content audit."""

    issues: list[A11yIssue]
    reading_grade: float
    target_grade: float

    @property
    def passed(self) -> bool:
        return len(self.critical_issues) == 0 and len(self.high_issues) == 0

    @property
    def critical_issues(self) -> list[A11yIssue]:
        return [i for i in self.issues if i.severity == A11ySeverity.CRITICAL]

    @property
    def high_issues(self) -> list[A11yIssue]:
        return [i for i in self.issues if i.severity == A11ySeverity.HIGH]

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    @property
    def label(self) -> str:
        if not self.issues:
            return "Pass"
        if self.critical_issues:
            return "Fail (critical issues)"
        if self.high_issues:
            return "Fail (high severity issues)"
        return "Pass (with warnings)"

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "label": self.label,
            "issue_count": self.issue_count,
            "reading_grade": self.reading_grade,
            "target_grade": self.target_grade,
            "issues": [i.to_dict() for i in self.issues],
        }


# "Click here" and similar anti-patterns
CLICK_HERE_PATTERNS = [
    r"\bclick here\b",
    r"\btap here\b",
    r"\bpress here\b",
    r"\bhere\b(?=\s*(?:to|for)\b)",
    r"\bclick this\b",
    r"\bclick the link\b",
    r"\bfollow this link\b",
]

# Emoji detection (broad Unicode ranges)
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"  # dingbats
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended
    "\U00002600-\U000026FF"  # misc symbols
    "]+",
    flags=re.UNICODE,
)

# ALL CAPS pattern (3+ consecutive uppercase words)
ALL_CAPS_PATTERN = re.compile(r"\b[A-Z]{2,}(?:\s+[A-Z]{2,}){0,}\b")

# Known abbreviations that are fine in ALL CAPS
ALLOWED_CAPS = {
    "API", "URL", "HTML", "CSS", "JS", "JSON", "XML", "SQL", "HTTP", "HTTPS",
    "REST", "SDK", "CLI", "UI", "UX", "ID", "FAQ", "PDF", "CSV", "AWS",
    "GCP", "CI", "CD", "AM", "PM", "EST", "PST", "UTC", "WCAG", "ARIA",
    "OK", "US", "EU", "UK",
}


class A11yChecker:
    """Checks content for WCAG text-level accessibility issues."""

    def __init__(self, target_grade: float = 8.0, max_emoji_per_100_words: int = 3):
        self.target_grade = target_grade
        self.max_emoji_per_100_words = max_emoji_per_100_words
        self._scorer = ReadabilityScorer()

    def check(self, text: str) -> A11yResult:
        """Run all accessibility checks on text."""
        issues = []
        readability = self._scorer.score(text)

        issues.extend(self._check_reading_level(readability))
        issues.extend(self._check_complex_sentences(text, readability))
        issues.extend(self._check_all_caps(text))
        issues.extend(self._check_emoji_overuse(text, readability.word_count))
        issues.extend(self._check_link_text(text))
        issues.extend(self._check_alt_text_references(text))

        return A11yResult(
            issues=issues,
            reading_grade=readability.flesch_kincaid_grade,
            target_grade=self.target_grade,
        )

    def _check_reading_level(self, readability) -> list[A11yIssue]:
        """Check if reading level exceeds target."""
        if readability.flesch_kincaid_grade > self.target_grade:
            return [A11yIssue(
                rule="reading-level",
                severity=A11ySeverity.HIGH,
                message=f"Reading level is grade {readability.flesch_kincaid_grade}, target is grade {self.target_grade} or lower",
                wcag_criterion="3.1.5 Reading Level",
                suggestion="Simplify sentences, use shorter words, break up complex ideas",
            )]
        return []

    def _check_complex_sentences(self, text: str, readability) -> list[A11yIssue]:
        """Flag sentences that are too long."""
        issues = []
        if readability.max_sentence_length > 25:
            # Find the long sentences
            sentences = re.split(r"[.!?]+", text)
            long_sentences = []
            for s in sentences:
                words = re.findall(r"[a-zA-Z']+", s)
                if len(words) > 25:
                    preview = " ".join(words[:8]) + "..."
                    long_sentences.append(preview)

            issues.append(A11yIssue(
                rule="sentence-length",
                severity=A11ySeverity.MEDIUM,
                message=f"Found {len(long_sentences)} sentence(s) over 25 words",
                wcag_criterion="3.1.5 Reading Level",
                suggestion="Break long sentences into shorter ones. Aim for 15-20 words per sentence.",
                matches=long_sentences,
            ))
        return issues

    def _check_all_caps(self, text: str) -> list[A11yIssue]:
        """Check for ALL CAPS usage that isn't an abbreviation."""
        matches = ALL_CAPS_PATTERN.findall(text)
        bad_caps = [m for m in matches if m not in ALLOWED_CAPS and len(m) > 2]
        if bad_caps:
            return [A11yIssue(
                rule="no-all-caps",
                severity=A11ySeverity.MEDIUM,
                message=f"Found {len(bad_caps)} ALL CAPS instance(s) — screen readers may spell these letter by letter",
                wcag_criterion="1.3.1 Info and Relationships",
                suggestion="Use sentence case or title case instead of ALL CAPS",
                matches=bad_caps,
            )]
        return []

    def _check_emoji_overuse(self, text: str, word_count: int) -> list[A11yIssue]:
        """Check for excessive emoji usage."""
        emojis = EMOJI_PATTERN.findall(text)
        emoji_count = sum(len(e) for e in emojis)

        if word_count == 0:
            threshold = self.max_emoji_per_100_words
        else:
            threshold = (self.max_emoji_per_100_words * word_count) / 100

        if emoji_count > max(self.max_emoji_per_100_words, threshold):
            return [A11yIssue(
                rule="emoji-overuse",
                severity=A11ySeverity.MEDIUM,
                message=f"Found {emoji_count} emoji(s) — screen readers announce each one individually",
                wcag_criterion="1.1.1 Non-text Content",
                suggestion=f"Limit to {self.max_emoji_per_100_words} emoji per 100 words. Each emoji is read aloud by screen readers.",
                matches=[e for e in emojis],
            )]
        return []

    def _check_link_text(self, text: str) -> list[A11yIssue]:
        """Check for 'click here' and similar anti-patterns."""
        text_lower = text.lower()
        found = []
        for pattern in CLICK_HERE_PATTERNS:
            matches = re.findall(pattern, text_lower)
            found.extend(matches)

        if found:
            return [A11yIssue(
                rule="descriptive-link-text",
                severity=A11ySeverity.HIGH,
                message=f"Found {len(found)} 'click here' pattern(s) — link text should describe the destination",
                wcag_criterion="2.4.4 Link Purpose",
                suggestion="Replace 'click here' with descriptive text: 'View pricing details' instead of 'Click here to see pricing'",
                matches=found,
            )]
        return []

    def _check_alt_text_references(self, text: str) -> list[A11yIssue]:
        """Check for image references that might need alt text."""
        issues = []

        # Check for markdown images without alt text
        empty_alt = re.findall(r"!\[\]\(", text)
        if empty_alt:
            issues.append(A11yIssue(
                rule="image-alt-text",
                severity=A11ySeverity.CRITICAL,
                message=f"Found {len(empty_alt)} image(s) without alt text",
                wcag_criterion="1.1.1 Non-text Content",
                suggestion="Add descriptive alt text to all informative images: ![Description of image](url)",
            ))

        # Check for alt text that's just a filename
        filename_alt = re.findall(r"!\[[\w-]+\.\w{3,4}\]", text)
        if filename_alt:
            issues.append(A11yIssue(
                rule="meaningful-alt-text",
                severity=A11ySeverity.HIGH,
                message=f"Found {len(filename_alt)} image(s) with filename as alt text",
                wcag_criterion="1.1.1 Non-text Content",
                suggestion="Replace filenames with descriptive alt text",
                matches=filename_alt,
            ))

        return issues

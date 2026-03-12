"""Content design lint rules for automated quality checks."""

import re
from dataclasses import dataclass, field
from enum import Enum


class LintSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintResult:
    """Result of a single lint rule check."""

    rule: str
    passed: bool
    severity: LintSeverity
    message: str
    suggestion: str = ""
    matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {
            "rule": self.rule,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.suggestion:
            d["suggestion"] = self.suggestion
        if self.matches:
            d["matches"] = self.matches
        return d


# Common action verbs for CTAs
ACTION_VERBS = {
    "get", "start", "try", "create", "build", "join", "see", "view",
    "explore", "discover", "learn", "download", "sign", "log", "open",
    "launch", "begin", "add", "save", "send", "submit", "buy", "shop",
    "order", "book", "reserve", "schedule", "claim", "grab", "unlock",
    "activate", "enable", "upgrade", "continue", "complete", "finish",
    "check", "find", "search", "browse", "watch", "play", "read",
    "invite", "share", "connect", "set", "go", "take", "make",
}

# Resolution/action words that make error messages actionable
RESOLUTION_PATTERNS = [
    r"\btry\b", r"\bcheck\b", r"\bensure\b", r"\bverify\b",
    r"\bcontact\b", r"\breach out\b", r"\bretry\b", r"\brefresh\b",
    r"\bupdate\b", r"\brestart\b", r"\bclear\b", r"\breset\b",
    r"\bclick\b", r"\btap\b", r"\bselect\b", r"\bgo to\b",
    r"\bvisit\b", r"\bnavigate\b", r"\bsee\b", r"\blearn more\b",
    r"\bhere's what\b", r"\byou can\b", r"\bto fix\b",
]

# Passive voice indicators
PASSIVE_PATTERNS = [
    r"\b(?:is|are|was|were|been|being)\s+(?:\w+ed|made|done|sent|shown|taken|given)\b",
    r"\bhas been\s+\w+ed\b",
    r"\bhave been\s+\w+ed\b",
    r"\bwill be\s+\w+ed\b",
    r"\bcan be\s+\w+ed\b",
]

# Default jargon list
DEFAULT_JARGON = [
    "leverage", "utilize", "facilitate", "synergy", "paradigm",
    "scalable", "robust", "seamless", "cutting-edge", "best-in-class",
    "end-to-end", "mission-critical", "value-add", "ecosystem",
    "bandwidth", "circle back", "deep dive", "move the needle",
    "low-hanging fruit", "boil the ocean", "bleeding edge",
    "disrupt", "pivot", "iterate", "align", "incentivize",
    "operationalize", "actualize", "ideate",
]

# Exclusionary terms and their alternatives
EXCLUSIONARY_TERMS = {
    "whitelist": "allowlist",
    "blacklist": "blocklist",
    "master": "main/primary",
    "slave": "replica/secondary",
    "dummy": "placeholder/sample",
    "sanity check": "quick check/smoke test",
    "grandfathered": "legacy/exempt",
    "guys": "everyone/team/folks",
    "manpower": "workforce/staffing",
    "man-hours": "person-hours/work hours",
    "cripple": "disable/limit",
    "lame": "inadequate/insufficient",
    "crazy": "unexpected/surprising",
    "insane": "extreme/intense",
}


class ContentLinter:
    """Runs content quality lint rules against text.

    When ``prefer_consistency=True``, the linter relaxes character-limit
    enforcement from *error* to *info* and adds a 20 % headroom buffer.
    This reflects the principle that sometimes concision should be
    sacrificed for consistency across a set of related strings (e.g.
    keeping parallel menu items or button labels at the same length even
    if one exceeds the ideal limit).
    """

    def __init__(
        self,
        custom_jargon: list[str] | None = None,
        custom_exclusionary: dict[str, str] | None = None,
        max_button_chars: int = 40,
        max_notification_chars: int = 120,
        prefer_consistency: bool = False,
    ):
        self.jargon_list = DEFAULT_JARGON + (custom_jargon or [])
        self.exclusionary_terms = {**EXCLUSIONARY_TERMS, **(custom_exclusionary or {})}
        self.max_button_chars = max_button_chars
        self.max_notification_chars = max_notification_chars
        self.prefer_consistency = prefer_consistency

    def lint(self, text: str, content_type: str = "general") -> list[LintResult]:
        """Run all applicable lint rules on text.

        Args:
            text: The content to lint.
            content_type: One of "general", "cta", "error", "button",
                         "notification", "microcopy".
        """
        results = []

        # Universal rules
        results.append(self._check_jargon(text))
        results.append(self._check_inclusive_language(text))
        results.append(self._check_passive_voice(text))

        # Type-specific rules
        if content_type in ("cta", "button"):
            results.append(self._check_cta_action_verb(text))
            results.append(self._check_character_limit(text, self.max_button_chars, "button"))

        if content_type == "error":
            results.append(self._check_error_actionable(text))

        if content_type == "notification":
            results.append(self._check_character_limit(text, self.max_notification_chars, "notification"))

        if content_type == "microcopy":
            results.append(self._check_passive_voice(text))

        return results

    def lint_all(self, text: str) -> list[LintResult]:
        """Run all rules regardless of content type."""
        results = []
        results.append(self._check_jargon(text))
        results.append(self._check_inclusive_language(text))
        results.append(self._check_passive_voice(text))
        results.append(self._check_cta_action_verb(text))
        results.append(self._check_error_actionable(text))
        results.append(self._check_character_limit(text, self.max_button_chars, "button"))
        results.append(self._check_consistency(text))
        return results

    def _check_cta_action_verb(self, text: str) -> LintResult:
        """Check that CTA text starts with an action verb."""
        first_word = text.strip().split()[0].lower() if text.strip() else ""
        passed = first_word in ACTION_VERBS
        return LintResult(
            rule="cta-action-verb",
            passed=passed,
            severity=LintSeverity.ERROR,
            message=(
                f"CTA starts with action verb '{first_word}'"
                if passed
                else f"CTA should start with an action verb, found '{first_word}'"
            ),
            suggestion="" if passed else f"Try starting with: {', '.join(sorted(list(ACTION_VERBS)[:8]))}...",
            matches=[] if passed else [first_word],
        )

    def _check_error_actionable(self, text: str) -> LintResult:
        """Check that error message contains resolution/action language."""
        text_lower = text.lower()
        found = [p for p in RESOLUTION_PATTERNS if re.search(p, text_lower)]
        passed = len(found) > 0
        return LintResult(
            rule="error-actionable",
            passed=passed,
            severity=LintSeverity.ERROR,
            message=(
                "Error message contains actionable resolution language"
                if passed
                else "Error message has no resolution guidance"
            ),
            suggestion="" if passed else "Add what the user can do: 'Try refreshing', 'Check your connection', etc.",
        )

    def _check_passive_voice(self, text: str) -> LintResult:
        """Check for passive voice in microcopy."""
        text_lower = text.lower()
        matches = []
        for pattern in PASSIVE_PATTERNS:
            found = re.findall(pattern, text_lower)
            matches.extend(found)
        passed = len(matches) == 0
        return LintResult(
            rule="no-passive-voice",
            passed=passed,
            severity=LintSeverity.WARNING,
            message=(
                "No passive voice detected"
                if passed
                else f"Found {len(matches)} passive voice instance(s)"
            ),
            suggestion="" if passed else "Rewrite in active voice: 'We sent your email' instead of 'Your email was sent'",
            matches=matches,
        )

    def _check_character_limit(self, text: str, limit: int, element: str) -> LintResult:
        """Check text length against character limit.

        When ``prefer_consistency`` is enabled, the limit gets a 20 %
        buffer and violations are downgraded from *error* to *info*,
        reflecting that keeping parallel strings consistent can be
        more important than strict brevity.
        """
        char_count = len(text.strip())

        if self.prefer_consistency:
            # Relaxed mode: 20% headroom, info-level only
            relaxed_limit = int(limit * 1.2)
            passed = char_count <= relaxed_limit
            severity = LintSeverity.INFO
            if passed:
                if char_count > limit:
                    msg = (
                        f"{element.capitalize()} text is {char_count} chars "
                        f"(soft limit: {limit}, consistency allowance: {relaxed_limit})"
                    )
                else:
                    msg = f"{element.capitalize()} text is {char_count} chars (limit: {limit})"
                suggestion = ""
            else:
                msg = (
                    f"{element.capitalize()} text is {char_count} chars, "
                    f"exceeds even the consistency allowance of {relaxed_limit} chars"
                )
                suggestion = f"Shorten to {relaxed_limit} characters or fewer"
        else:
            # Strict mode (default)
            passed = char_count <= limit
            severity = LintSeverity.ERROR
            msg = (
                f"{element.capitalize()} text is {char_count} chars (limit: {limit})"
                if passed
                else f"{element.capitalize()} text is {char_count} chars, exceeds {limit} char limit"
            )
            suggestion = "" if passed else f"Shorten to {limit} characters or fewer"

        return LintResult(
            rule=f"{element}-char-limit",
            passed=passed,
            severity=severity,
            message=msg,
            suggestion=suggestion,
        )

    def _check_jargon(self, text: str) -> LintResult:
        """Check for jargon and buzzwords."""
        text_lower = text.lower()
        found = [j for j in self.jargon_list if j.lower() in text_lower]
        passed = len(found) == 0
        return LintResult(
            rule="no-jargon",
            passed=passed,
            severity=LintSeverity.WARNING,
            message=(
                "No jargon detected"
                if passed
                else f"Found {len(found)} jargon term(s)"
            ),
            suggestion="" if passed else "Replace with plain language alternatives",
            matches=found,
        )

    def _check_inclusive_language(self, text: str) -> LintResult:
        """Check for exclusionary terms."""
        text_lower = text.lower()
        found = {}
        for term, replacement in self.exclusionary_terms.items():
            if term.lower() in text_lower:
                found[term] = replacement
        passed = len(found) == 0
        return LintResult(
            rule="inclusive-language",
            passed=passed,
            severity=LintSeverity.ERROR,
            message=(
                "No exclusionary language detected"
                if passed
                else f"Found {len(found)} exclusionary term(s)"
            ),
            suggestion=(
                ""
                if passed
                else "Replace: " + ", ".join(f"'{k}' → '{v}'" for k, v in found.items())
            ),
            matches=list(found.keys()),
        )

    def _check_consistency(self, text: str) -> LintResult:
        """Check for inconsistent terminology within the text."""
        # Common pairs that should be consistent
        term_pairs = [
            (r"\blog in\b", r"\blogin\b", "log in/login"),
            (r"\bsign up\b", r"\bsignup\b", "sign up/signup"),
            (r"\be-mail\b", r"\bemail\b", "e-mail/email"),
            (r"\bset up\b", r"\bsetup\b", "set up/setup"),
            (r"\bcheck out\b", r"\bcheckout\b", "check out/checkout"),
        ]
        text_lower = text.lower()
        inconsistencies = []
        for pattern_a, pattern_b, label in term_pairs:
            has_a = bool(re.search(pattern_a, text_lower))
            has_b = bool(re.search(pattern_b, text_lower))
            if has_a and has_b:
                inconsistencies.append(label)

        passed = len(inconsistencies) == 0
        return LintResult(
            rule="consistent-terminology",
            passed=passed,
            severity=LintSeverity.WARNING,
            message=(
                "Terminology is consistent"
                if passed
                else f"Inconsistent terminology: {', '.join(inconsistencies)}"
            ),
            suggestion="" if passed else "Pick one form and use it consistently throughout",
            matches=inconsistencies,
        )

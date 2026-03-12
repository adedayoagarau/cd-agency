"""Constraint validation for content design outputs.

Validates content against UI element constraints — character limits,
platform conventions, localization expansion, and accessibility rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ConstraintViolation:
    """A single constraint violation found during validation."""

    rule: str
    severity: str  # "error", "warning", "info"
    message: str
    value: Any = None
    limit: Any = None


@dataclass
class ConstraintResult:
    """Result of constraint validation."""

    violations: list[ConstraintViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(v.severity == "error" for v in self.violations)

    @property
    def errors(self) -> list[ConstraintViolation]:
        return [v for v in self.violations if v.severity == "error"]

    @property
    def warnings(self) -> list[ConstraintViolation]:
        return [v for v in self.violations if v.severity == "warning"]

    def summary(self) -> str:
        """Human-readable summary."""
        if not self.violations:
            return "All constraints passed."
        errs = len(self.errors)
        warns = len(self.warnings)
        parts = []
        if errs:
            parts.append(f"{errs} error(s)")
        if warns:
            parts.append(f"{warns} warning(s)")
        return f"Constraint check: {', '.join(parts)}"


# Character limits by UI element type (max characters)
ELEMENT_CHAR_LIMITS: dict[str, dict[str, Any]] = {
    "button": {"max": 25, "label": "Button text"},
    "button_secondary": {"max": 30, "label": "Secondary button text"},
    "nav_label": {"max": 20, "label": "Navigation label"},
    "tab_label": {"max": 18, "label": "Tab label"},
    "tooltip": {"max": 120, "label": "Tooltip text"},
    "toast": {"max": 60, "label": "Toast/snackbar message"},
    "push_title": {"max": 50, "label": "Push notification title"},
    "push_body": {"max": 120, "label": "Push notification body"},
    "email_subject": {"max": 50, "label": "Email subject line"},
    "email_preview": {"max": 100, "label": "Email preview text"},
    "form_label": {"max": 40, "label": "Form field label"},
    "placeholder": {"max": 45, "label": "Placeholder text"},
    "inline_error": {"max": 80, "label": "Inline validation error"},
    "modal_headline": {"max": 60, "label": "Modal headline"},
    "modal_body": {"max": 250, "label": "Modal body text"},
    "empty_state_headline": {"max": 50, "label": "Empty state headline"},
    "empty_state_body": {"max": 150, "label": "Empty state body"},
    "badge": {"max": 20, "label": "Badge/tag label"},
    "banner": {"max": 150, "label": "Banner message"},
    "breadcrumb": {"max": 25, "label": "Breadcrumb segment"},
    "sms": {"max": 160, "label": "SMS message"},
}

# Localization expansion factors by language
EXPANSION_FACTORS: dict[str, float] = {
    "de": 1.35,   # German
    "fr": 1.20,   # French
    "es": 1.25,   # Spanish
    "it": 1.20,   # Italian
    "pt": 1.25,   # Portuguese
    "nl": 1.25,   # Dutch
    "pl": 1.25,   # Polish
    "fi": 1.40,   # Finnish
    "sv": 1.15,   # Swedish
    "ru": 1.15,   # Russian
    "ja": 0.80,   # Japanese (shorter in chars, but chars are wider)
    "zh": 0.70,   # Chinese
    "ko": 0.85,   # Korean
    "ar": 1.00,   # Arabic (similar length)
}

# Platform conventions
PLATFORM_CONVENTIONS: dict[str, dict[str, Any]] = {
    "ios": {
        "button_case": "title",
        "alert_destructive_position": "left",
        "alert_confirm_position": "right",
        "interaction_verb": "Tap",
        "settings_term": "Settings",
        "push_title_max": 50,
        "push_body_max": 120,
    },
    "android": {
        "button_case": "sentence",
        "alert_destructive_position": "right",
        "alert_confirm_position": "right",
        "interaction_verb": "Tap",
        "settings_term": "Settings",
        "push_title_max": 40,
        "push_body_max": 90,
    },
    "web": {
        "button_case": "varies",
        "alert_destructive_position": "right",
        "alert_confirm_position": "right",
        "interaction_verb": "Click",
        "settings_term": "Settings",
        "push_title_max": 50,
        "push_body_max": 120,
    },
}


def validate_character_limit(
    text: str,
    element_type: str,
    *,
    custom_limit: int | None = None,
) -> ConstraintResult:
    """Validate text against character limits for a UI element type."""
    result = ConstraintResult()

    limit_info = ELEMENT_CHAR_LIMITS.get(element_type)
    max_chars = custom_limit or (limit_info["max"] if limit_info else None)

    if max_chars is None:
        return result  # No limit to check

    label = limit_info["label"] if limit_info else element_type
    text_len = len(text.strip())

    if text_len > max_chars:
        result.violations.append(ConstraintViolation(
            rule="character_limit",
            severity="error",
            message=f"{label} exceeds {max_chars} char limit ({text_len} chars)",
            value=text_len,
            limit=max_chars,
        ))
    elif text_len > max_chars * 0.9:
        result.violations.append(ConstraintViolation(
            rule="character_limit_warning",
            severity="warning",
            message=f"{label} is {text_len} chars — close to {max_chars} char limit (90%+). May truncate on small screens.",
            value=text_len,
            limit=max_chars,
        ))

    return result


def validate_localization(
    text: str,
    element_type: str,
    target_language: str,
    *,
    custom_limit: int | None = None,
) -> ConstraintResult:
    """Check if text will exceed element limits after translation expansion."""
    result = ConstraintResult()

    factor = EXPANSION_FACTORS.get(target_language)
    if factor is None:
        return result

    limit_info = ELEMENT_CHAR_LIMITS.get(element_type)
    max_chars = custom_limit or (limit_info["max"] if limit_info else None)

    if max_chars is None:
        return result

    expanded_len = int(len(text.strip()) * factor)
    lang_name = target_language.upper()

    if expanded_len > max_chars:
        result.violations.append(ConstraintViolation(
            rule="localization_expansion",
            severity="warning",
            message=(
                f"Text will expand to ~{expanded_len} chars in {lang_name} "
                f"(factor: {factor}x), exceeding {max_chars} char limit. "
                f"Shorten the English source to ≤ {int(max_chars / factor)} chars."
            ),
            value=expanded_len,
            limit=max_chars,
        ))

    return result


def validate_platform_conventions(
    text: str,
    element_type: str,
    platform: str,
) -> ConstraintResult:
    """Validate text against platform-specific conventions."""
    result = ConstraintResult()

    conventions = PLATFORM_CONVENTIONS.get(platform.lower())
    if not conventions:
        return result

    # Check button capitalization
    if element_type in ("button", "button_secondary"):
        expected_case = conventions["button_case"]
        if expected_case == "title":
            # Title Case: first letter of each word capitalized
            words = text.strip().split()
            if words and not all(w[0].isupper() for w in words if w and w[0].isalpha()):
                result.violations.append(ConstraintViolation(
                    rule="platform_case",
                    severity="warning",
                    message=f"{platform.upper()} uses Title Case for buttons. "
                            f'Consider: "{text.strip().title()}"',
                    value=text.strip(),
                ))
        elif expected_case == "sentence":
            # Sentence case: only first word capitalized
            words = text.strip().split()
            if len(words) > 1 and all(w[0].isupper() for w in words if w and w[0].isalpha()):
                result.violations.append(ConstraintViolation(
                    rule="platform_case",
                    severity="warning",
                    message=f"{platform.upper()} uses sentence case for buttons. "
                            f'Consider: "{words[0]} {" ".join(w.lower() for w in words[1:])}"',
                    value=text.strip(),
                ))

    # Check platform-specific push notification limits
    if element_type == "push_title":
        platform_max = conventions.get("push_title_max")
        if platform_max and len(text.strip()) > platform_max:
            result.violations.append(ConstraintViolation(
                rule="platform_push_title_limit",
                severity="warning",
                message=f"{platform.upper()} push title truncates at {platform_max} chars "
                        f"({len(text.strip())} chars provided).",
                value=len(text.strip()),
                limit=platform_max,
            ))

    if element_type == "push_body":
        platform_max = conventions.get("push_body_max")
        if platform_max and len(text.strip()) > platform_max:
            result.violations.append(ConstraintViolation(
                rule="platform_push_body_limit",
                severity="warning",
                message=f"{platform.upper()} push body truncates at {platform_max} chars "
                        f"on lock screen ({len(text.strip())} chars provided).",
                value=len(text.strip()),
                limit=platform_max,
            ))

    # Check interaction verbs
    interaction_verb = conventions["interaction_verb"]
    wrong_verbs = {"Click", "Tap", "Press", "Select"} - {interaction_verb}
    text_lower = text.lower()
    for wrong in wrong_verbs:
        if wrong.lower() in text_lower:
            result.violations.append(ConstraintViolation(
                rule="platform_interaction_verb",
                severity="info",
                message=f'{platform.upper()} convention: use "{interaction_verb}" instead of "{wrong}".',
                value=wrong,
            ))
            break  # Only flag once

    return result


def validate_accessibility(text: str, element_type: str) -> ConstraintResult:
    """Check content for common accessibility issues."""
    result = ConstraintResult()
    text_stripped = text.strip()

    # Check for "click here" anti-pattern
    if "click here" in text_stripped.lower():
        result.violations.append(ConstraintViolation(
            rule="a11y_link_text",
            severity="error",
            message='"Click here" is meaningless to screen reader users scanning links. '
                    "Use descriptive link text that explains the destination.",
            value=text_stripped,
        ))

    # Check for "learn more" without context
    if text_stripped.lower() == "learn more":
        result.violations.append(ConstraintViolation(
            rule="a11y_vague_link",
            severity="warning",
            message='"Learn more" is ambiguous for screen readers. '
                    'Use "Learn more about [topic]" for better accessibility.',
            value=text_stripped,
        ))

    # Check for ALL CAPS (hard to read, screen readers may spell it out)
    words = text_stripped.split()
    all_caps_words = [w for w in words if w.isupper() and len(w) > 3]
    if len(all_caps_words) >= 2:
        result.violations.append(ConstraintViolation(
            rule="a11y_all_caps",
            severity="warning",
            message="Multiple ALL CAPS words detected. All-caps text is harder to read "
                    "and may be spelled out letter-by-letter by screen readers.",
            value=", ".join(all_caps_words),
        ))

    # Check placeholder text warnings
    if element_type == "placeholder":
        result.violations.append(ConstraintViolation(
            rule="a11y_placeholder_warning",
            severity="info",
            message="Placeholder text disappears on focus. Never use it as the only "
                    "label — always pair with a visible label above the field.",
        ))

    return result


def validate_content(
    text: str,
    element_type: str,
    *,
    platform: str | None = None,
    target_language: str | None = None,
    custom_limit: int | None = None,
) -> ConstraintResult:
    """Run all constraint validations on a piece of content.

    Args:
        text: The content to validate.
        element_type: UI element type (e.g., "button", "tooltip", "push_body").
        platform: Target platform ("ios", "android", "web").
        target_language: ISO code for translation target (e.g., "de", "fr").
        custom_limit: Override the default character limit.

    Returns:
        Combined ConstraintResult with all violations.
    """
    combined = ConstraintResult()

    # Character limit check
    char_result = validate_character_limit(text, element_type, custom_limit=custom_limit)
    combined.violations.extend(char_result.violations)

    # Localization expansion check
    if target_language:
        loc_result = validate_localization(
            text, element_type, target_language, custom_limit=custom_limit,
        )
        combined.violations.extend(loc_result.violations)

    # Platform convention check
    if platform:
        plat_result = validate_platform_conventions(text, element_type, platform)
        combined.violations.extend(plat_result.violations)

    # Accessibility check
    a11y_result = validate_accessibility(text, element_type)
    combined.violations.extend(a11y_result.violations)

    return combined


def get_element_limit(element_type: str) -> int | None:
    """Get the default character limit for a UI element type."""
    info = ELEMENT_CHAR_LIMITS.get(element_type)
    return info["max"] if info else None


def list_element_types() -> list[dict[str, Any]]:
    """List all known UI element types and their limits."""
    return [
        {"type": k, "max_chars": v["max"], "label": v["label"]}
        for k, v in ELEMENT_CHAR_LIMITS.items()
    ]

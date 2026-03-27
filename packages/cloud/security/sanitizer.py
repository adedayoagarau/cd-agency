"""Input sanitization helpers for user-supplied content."""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

_SCRIPT_TAG_RE = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
_EVENT_HANDLER_RE = re.compile(r"""\s+on\w+\s*=\s*["'][^"']*["']""", re.IGNORECASE)
_STYLE_EXPRESSION_RE = re.compile(r"expression\s*\(", re.IGNORECASE)
_JAVASCRIPT_URL_RE = re.compile(r"javascript\s*:", re.IGNORECASE)
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def sanitize_input(text: str) -> str:
    """Strip characters and patterns commonly used in XSS / injection attacks.

    This is a *best-effort* filter intended for plain-text user input (not
    HTML).  It removes ``<script>`` blocks, inline event handlers, and
    ``javascript:`` URLs, then collapses excessive whitespace.
    """
    result = _SCRIPT_TAG_RE.sub("", text)
    result = _EVENT_HANDLER_RE.sub("", result)
    result = _JAVASCRIPT_URL_RE.sub("", result)
    result = _STYLE_EXPRESSION_RE.sub("", result)

    # Strip null bytes
    result = result.replace("\x00", "")

    # Collapse runs of whitespace (but preserve newlines)
    result = re.sub(r"[^\S\n]+", " ", result)

    return result.strip()


def sanitize_html(html: str) -> str:
    """Remove dangerous HTML constructs while keeping benign markup.

    Removes:
    - ``<script>`` tags and their contents
    - Inline event-handler attributes (``onclick``, ``onerror``, etc.)
    - ``javascript:`` URLs
    - CSS ``expression()`` calls
    """
    result = _SCRIPT_TAG_RE.sub("", html)
    result = _EVENT_HANDLER_RE.sub("", result)
    result = _JAVASCRIPT_URL_RE.sub("", result)
    result = _STYLE_EXPRESSION_RE.sub("", result)
    return result.strip()


def validate_slug(slug: str) -> bool:
    """Return *True* if *slug* contains only lowercase alphanumeric characters and hyphens.

    Slugs must start and end with an alphanumeric character; consecutive
    hyphens are not allowed.
    """
    if not slug:
        return False
    return _SLUG_RE.match(slug) is not None

"""Extract hardcoded UI strings from JS/TS/Vue/HTML files.

Uses regex patterns and lightweight AST-style parsing to find user-facing
strings that should be reviewed by content design agents.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

EXTENSIONS = {".js", ".jsx", ".ts", ".tsx", ".vue", ".html"}

# Strings shorter than this are likely CSS values, keys, or config tokens
MIN_LENGTH = 3

# Strings matching any of these patterns are NOT user-facing text
SKIP_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^[a-z][a-zA-Z0-9]*$"),          # camelCase identifiers
    re.compile(r"^[A-Z][A-Z0-9_]+$"),             # CONSTANT_CASE
    re.compile(r"^[a-z]+[-_.][a-z]", re.I),       # kebab/dot/snake keys
    re.compile(r"^https?://"),                     # URLs
    re.compile(r"^[/#.]"),                         # paths / CSS selectors
    re.compile(r"^\d"),                            # starts with digit
    re.compile(r"^[{<\[]"),                        # template / JSX / JSON
    re.compile(r"^(true|false|null|undefined)$"),  # JS literals
    re.compile(r"^(GET|POST|PUT|DELETE|PATCH)$"),  # HTTP methods
    re.compile(r"^(div|span|button|input|form|img|svg|path|a|p|h[1-6])$"),  # tags
    re.compile(r"^(click|change|submit|focus|blur|keydown|keyup|scroll)$"),  # events
    re.compile(r"^(flex|grid|block|none|auto|inherit|relative|absolute)$"),  # CSS
    re.compile(r"^(useState|useEffect|useRef|useCallback|useMemo)$"),  # React hooks
    re.compile(r"^(import|export|require|module|console)\b"),  # JS keywords
    re.compile(r"^rgba?\("),                       # color functions
    re.compile(r"^\d+(\.\d+)?(px|rem|em|%|vh|vw|s|ms)$"),  # CSS units
    re.compile(r"^[a-z]+\.(js|ts|jsx|tsx|css|svg|png|jpg|json)$"),  # filenames
    re.compile(r"^(data-|aria-|x-|v-|ng-)"),       # HTML/framework attrs
]

# Patterns that strongly signal user-facing text
UI_BOOST_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\s"),                             # contains whitespace
    re.compile(r"[.!?]$"),                         # ends with punctuation
    re.compile(r"^[A-Z]"),                         # starts capitalised
]


@dataclass
class ExtractedString:
    """A hardcoded string found in source code."""

    value: str
    file: str
    line: int
    context: str  # surrounding code snippet

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "file": self.file,
            "line": self.line,
            "context": self.context,
        }


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

# Match string literals: "...", '...', `...` (backtick without ${} interpolation)
_STRING_RE = re.compile(
    r'''"((?:[^"\\]|\\.)*)"'''             # double-quoted
    r"""|'((?:[^'\\]|\\.)*)'"""            # single-quoted
    r"""|`((?:[^`\\$]|\\.)*)`""",          # simple template literal (no ${})
    re.DOTALL,
)

# Patterns indicating a string is in a UI-rendering context
_UI_CONTEXT_RE = re.compile(
    r"""(?:"""
    r"""(?:label|title|placeholder|alt|aria-label|message|text|heading"""
    r"""|description|tooltip|hint|caption|error|warning|info|success"""
    r"""|helperText|errorText|buttonText|header|subtitle|content)"""
    r"""\s*[:=]\s*$) |"""                  # prop/attr assignment before string
    r"""(?:>$) |"""                        # JSX child text
    r"""(?:t\(\s*$) |"""                   # i18n function (flag for review)
    r"""(?:innerHTML\s*=\s*$)""",
    re.IGNORECASE | re.VERBOSE,
)

# HTML visible-text contexts
_HTML_TEXT_TAGS = re.compile(
    r"<(?:p|h[1-6]|span|label|button|a|li|th|td|caption|figcaption"
    r"|legend|option|summary|title|dt|dd)\b[^>]*>([^<]+)<",
    re.IGNORECASE,
)


def _is_skippable(s: str) -> bool:
    """Return True if the string looks like a non-user-facing token."""
    if len(s) < MIN_LENGTH:
        return True
    for pat in SKIP_PATTERNS:
        if pat.search(s):
            return True
    return False


def _is_likely_ui(s: str, before_context: str) -> bool:
    """Heuristic: is this string probably user-facing?"""
    # If it's in a UI-context assignment, strong signal
    if _UI_CONTEXT_RE.search(before_context):
        return True
    # Boost if it looks like natural language
    boost = sum(1 for pat in UI_BOOST_PATTERNS if pat.search(s))
    return boost >= 2


def _get_line_context(lines: list[str], line_idx: int, window: int = 1) -> str:
    """Return a snippet of surrounding lines for context."""
    start = max(0, line_idx - window)
    end = min(len(lines), line_idx + window + 1)
    return "\n".join(lines[start:end]).strip()


def extract_strings_from_file(filepath: Path) -> list[ExtractedString]:
    """Extract candidate UI strings from a single file."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    lines = text.split("\n")
    results: list[ExtractedString] = []
    seen: set[str] = set()

    # --- Pass 1: regex string literal extraction ---
    for match in _STRING_RE.finditer(text):
        value = match.group(1) or match.group(2) or match.group(3)
        if value is None:
            continue
        value = value.strip()

        if _is_skippable(value):
            continue
        if value in seen:
            continue

        # Compute line number
        line_no = text[:match.start()].count("\n") + 1
        line_idx = line_no - 1

        # Get the text just before the string on the same line
        line_start = text.rfind("\n", 0, match.start()) + 1
        before = text[line_start:match.start()]

        if _is_likely_ui(value, before):
            seen.add(value)
            results.append(ExtractedString(
                value=value,
                file=str(filepath),
                line=line_no,
                context=_get_line_context(lines, line_idx),
            ))

    # --- Pass 2: HTML inner-text extraction (for .html and .vue files) ---
    if filepath.suffix in {".html", ".vue"}:
        for match in _HTML_TEXT_TAGS.finditer(text):
            value = match.group(1).strip()
            if _is_skippable(value):
                continue
            if value in seen:
                continue
            if "{{" in value:
                # Strip template interpolation markers for the text portion
                plain = re.sub(r"\{\{.*?\}\}", "", value).strip()
                if not plain or _is_skippable(plain):
                    continue
                value = plain

            line_no = text[:match.start()].count("\n") + 1
            seen.add(value)
            results.append(ExtractedString(
                value=value,
                file=str(filepath),
                line=line_no,
                context=_get_line_context(lines, line_no - 1),
            ))

    return results


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------

def scan_directory(root: Path, changed_files: list[str] | None = None) -> list[ExtractedString]:
    """Scan files for hardcoded UI strings.

    Args:
        root: The repository root to search.
        changed_files: If provided, only scan these files (for PR-scoped runs).
    """
    all_strings: list[ExtractedString] = []

    if changed_files:
        files = [Path(f) for f in changed_files if Path(f).suffix in EXTENSIONS]
    else:
        files = [p for p in root.rglob("*") if p.suffix in EXTENSIONS
                 and "node_modules" not in p.parts
                 and ".next" not in p.parts
                 and "dist" not in p.parts
                 and "build" not in p.parts
                 and "vendor" not in p.parts]

    for filepath in sorted(files):
        if not filepath.is_file():
            continue
        extracted = extract_strings_from_file(filepath)
        all_strings.extend(extracted)

    return all_strings


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI: extract strings and output JSON to stdout."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract hardcoded UI strings")
    parser.add_argument("root", nargs="?", default=".", help="Repository root")
    parser.add_argument(
        "--changed-files",
        nargs="*",
        default=None,
        help="Only scan these files (space-separated)",
    )
    parser.add_argument(
        "--max-strings",
        type=int,
        default=200,
        help="Maximum number of strings to extract (default: 200)",
    )
    args = parser.parse_args()

    strings = scan_directory(Path(args.root), args.changed_files)

    # Cap output to avoid overloading agent context windows
    if len(strings) > args.max_strings:
        strings = strings[:args.max_strings]

    output = {
        "total_found": len(strings),
        "strings": [s.to_dict() for s in strings],
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

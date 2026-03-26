"""Run cd-agency content design agents against extracted UI strings.

Reads extracted strings from ci/extract_strings.py, batches them, runs
the configured agents, and produces a Markdown report suitable for posting
as a GitHub PR comment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure the repo root is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from runtime.config import Config
from runtime.registry import AgentRegistry
from runtime.runner import AgentRunner

# ---------------------------------------------------------------------------
# Agent configuration
# ---------------------------------------------------------------------------

AUDIT_AGENTS: list[dict[str, Any]] = [
    {
        "slug": "microcopy-review-agent",
        "label": "Microcopy Review",
        "build_input": lambda strings: {
            "microcopy": "\n".join(
                f"- \"{s['value']}\" ({s['file']}:{s['line']})" for s in strings
            ),
            "ui_context": "Various UI locations across the codebase (PR diff)",
        },
    },
    {
        "slug": "tone-evaluation-agent",
        "label": "Tone Evaluation",
        "build_input": lambda strings: {
            "content": "\n".join(
                f"- \"{s['value']}\" ({s['file']}:{s['line']})" for s in strings
            ),
        },
    },
    {
        "slug": "accessibility-content-auditor",
        "label": "Accessibility Audit",
        "build_input": lambda strings: {
            "content": "\n".join(
                f"- \"{s['value']}\" ({s['file']}:{s['line']})" for s in strings
            ),
            "content_type": "web application UI strings",
        },
    },
    {
        "slug": "content-designer-generalist",
        "label": "Content Consistency",
        "build_input": lambda strings: {
            "content_or_context": (
                "Review the following UI strings for consistency in terminology, "
                "capitalization, punctuation, and phrasing patterns. Flag any "
                "inconsistencies and suggest standardized alternatives.\n\n"
                + "\n".join(
                    f"- \"{s['value']}\" ({s['file']}:{s['line']})" for s in strings
                )
            ),
        },
    },
]

# Maximum strings per agent batch to stay within context limits
MAX_STRINGS_PER_BATCH = 50


# ---------------------------------------------------------------------------
# Audit runner
# ---------------------------------------------------------------------------

def run_audit(strings_json: str) -> str:
    """Run all audit agents and return a Markdown report.

    Args:
        strings_json: JSON string from extract_strings.py output.

    Returns:
        Markdown-formatted report string.
    """
    data = json.loads(strings_json)
    strings: list[dict[str, Any]] = data.get("strings", [])

    if not strings:
        return _build_clean_report()

    config = Config.from_env()
    registry = AgentRegistry.from_directory(config.agents_dir)
    runner = AgentRunner(config)

    # Cap strings to avoid exceeding token limits
    batch = strings[:MAX_STRINGS_PER_BATCH]
    total_found = data.get("total_found", len(strings))

    sections: list[str] = []
    errors: list[str] = []

    for agent_cfg in AUDIT_AGENTS:
        slug = agent_cfg["slug"]
        label = agent_cfg["label"]
        agent = registry.get(slug)

        if agent is None:
            errors.append(f"Agent `{slug}` not found in registry")
            continue

        user_input = agent_cfg["build_input"](batch)

        try:
            output = runner.run(agent, user_input)
            sections.append(_format_agent_section(label, output.content))
        except Exception as e:
            errors.append(f"**{label}** failed: {e}")

    return _build_report(sections, errors, total_found, len(batch))


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _format_agent_section(label: str, content: str) -> str:
    """Format a single agent's output as a report section."""
    return f"### {label}\n\n{content}"


def _build_clean_report() -> str:
    """Report when no UI strings were found."""
    return (
        "## Content Audit Report\n\n"
        "No hardcoded UI strings were found in the changed files. "
        "Nothing to review.\n"
    )


def _build_report(
    sections: list[str],
    errors: list[str],
    total_found: int,
    reviewed: int,
) -> str:
    """Assemble the full Markdown report."""
    parts: list[str] = []

    parts.append("## Content Audit Report\n")
    parts.append(
        f"Scanned PR diff and found **{total_found}** hardcoded UI string(s). "
        f"Reviewed **{reviewed}** with 4 content design agents.\n"
    )

    parts.append("---\n")

    for section in sections:
        parts.append(section)
        parts.append("")

    if errors:
        parts.append("---\n")
        parts.append("### Errors\n")
        for err in errors:
            parts.append(f"- {err}")
        parts.append("")

    parts.append("---\n")
    parts.append(
        "*Powered by [cd-agency](https://github.com/adedayoagarau/cd-agency) "
        "content design agents.*\n"
    )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Read extracted strings from stdin or a file and output the report."""
    import argparse

    parser = argparse.ArgumentParser(description="Run content audit agents")
    parser.add_argument(
        "--input",
        default="-",
        help="Path to extracted strings JSON (default: stdin)",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="Path to write the Markdown report (default: stdout)",
    )
    args = parser.parse_args()

    if args.input == "-":
        strings_json = sys.stdin.read()
    else:
        strings_json = Path(args.input).read_text()

    report = run_audit(strings_json)

    if args.output == "-":
        sys.stdout.write(report)
    else:
        Path(args.output).write_text(report)


if __name__ == "__main__":
    main()

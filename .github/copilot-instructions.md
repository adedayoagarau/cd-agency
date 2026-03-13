# GitHub Copilot Instructions for CD Agency

This is a Content Design Agency — 17 specialized AI agents for UX writing and content design.

## Key context

- Python 3.10+, type hints, dataclasses, `from __future__ import annotations`
- CLI built with Click + Rich (`runtime/cli.py`)
- Agent definitions are Markdown files with YAML frontmatter in `content-design/`
- Scoring tools (readability, lint, a11y, voice) in `tools/` — work without API key
- 541 tests in `tests/` using pytest — run with `python -m pytest tests/`
- Config in `.cd-agency.yaml` or environment variables

## When writing code

- Follow existing patterns in `runtime/` and `tools/`
- Add tests for new features
- Use dataclasses for structured data, not dicts
- Use Click decorators for new CLI commands
- Import from `runtime.agent`, `runtime.registry`, `tools.scoring`, etc.

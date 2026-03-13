# CD Agency — Claude Code Instructions

This is a **Content Design Agency** — a collection of 17 specialized AI agents for UX writing, content design, and copy optimization. It is a Python package with a CLI, scoring tools, workflows, design system presets, a knowledge base, content versioning, and a TUI studio.

## Architecture

```
runtime/         → Core SDK: agent loading, registry, runner, CLI, memory, config
tools/           → Scoring tools: readability, linter, a11y, voice, export, analytics
content-design/  → 17 agent definition files (.md with YAML frontmatter)
workflows/       → 6 multi-agent pipeline definitions (.yaml)
presets/         → 4 design system voice profiles (Material, Polaris, Atlassian, Apple HIG)
knowledge/       → 52 curated content design resources (books, case studies, domains, patterns)
tests/           → 541 unit and integration tests (pytest)
```

## Key Commands

```bash
# Run the CLI
cd-agency agent list                    # List all 17 agents
cd-agency agent run error -i "..."     # Run an agent
cd-agency score all -i "..."           # Score content (readability, lint, a11y)
cd-agency workflow run content-audit    # Run a multi-agent pipeline
cd-agency interactive                   # Guided mode
cd-agency memory show                   # View project memory
cd-agency stats                         # Usage analytics

# Run tests
python -m pytest tests/ -v
```

## Development Conventions

- Python 3.10+, type hints, dataclasses
- `from __future__ import annotations` in every file
- Tests in `tests/`, one test file per module
- Agent definitions use YAML frontmatter in Markdown
- Config via `.cd-agency.yaml` or environment variables
- `ANTHROPIC_API_KEY` required for agent execution (not for scoring/linting)

## Agent Format

Agents are `.md` files in `content-design/` with YAML frontmatter defining name, inputs, outputs, tags, and related agents. The Markdown body contains the system prompt, critical rules, and few-shot examples. See `content-design/agent-template.md`.

## Adding Features

- New agents → `content-design/your-agent.md` or `cd-agency agent create`
- New lint rules → `tools/linter.py` + tests in `tests/test_linter.py`
- New workflows → `workflows/your-workflow.yaml`
- New presets → `presets/your-preset.yaml`
- New CLI commands → `runtime/cli.py`

## Testing

Always run `python -m pytest tests/` before committing. All 541 tests should pass.
Tests don't require an API key — they test agent loading, scoring, linting, and CLI commands.

# AI Agent Instructions for CD Agency

> This file provides context for AI coding assistants (Codex, Lovable, Bolt.new, Cursor, Replit, Windsurf, Claude Code, GitHub Copilot, etc.)

## What This Project Is

**CD Agency** is a Content Design Agency — a Python package with 17 specialized AI agents for UX writing, content design, and copy optimization. It includes a CLI, scoring tools, multi-agent workflows, design system presets, a knowledge base, content versioning, a TUI studio, and project memory.

## Quick Reference

| Component | Location | Description |
|-----------|----------|-------------|
| Agents | `content-design/*.md` | 17 agent definitions with YAML frontmatter |
| Runtime | `runtime/*.py` | Agent loading, registry, runner, CLI, config, memory |
| Tools | `tools/*.py` | Readability, linter, a11y, voice scoring, export, analytics |
| Workflows | `workflows/*.yaml` | 6 multi-agent pipelines |
| Presets | `presets/*.yaml` | 4 design system voice profiles |
| Tests | `tests/*.py` | 541 pytest unit and integration tests |

## Tech Stack

- **Language**: Python 3.10+
- **CLI**: Click + Rich
- **AI**: Anthropic Claude API (`anthropic` SDK)
- **Testing**: pytest
- **Config**: YAML (PyYAML)
- **Packaging**: setuptools via pyproject.toml

## Common Tasks

### Run tests
```bash
python -m pytest tests/ -v
```

### Add a new agent
```bash
cd-agency agent create  # Interactive wizard
# Or copy content-design/agent-template.md
```

### Run an agent
```bash
cd-agency agent run error-message-architect -i "404 page not found"
```

### Score content
```bash
cd-agency score all -i "Click here to submit your form" --json-output
```

### Run a workflow
```bash
cd-agency workflow run content-audit --input "Your UI text here"
```

## Architecture Patterns

1. **Agent Definition**: Markdown files with YAML frontmatter → parsed by `runtime/loader.py` → `Agent` dataclass
2. **Registry**: `runtime/registry.py` indexes agents for lookup by name, slug, alias, tag, or difficulty
3. **Runner**: `runtime/runner.py` sends Agent's system prompt + user input to Claude API
4. **Scoring**: Independent tools (readability, lint, a11y, voice) that work without an API key
5. **Workflows**: YAML pipelines that chain agents together with data passing between steps
6. **Memory**: JSON store in `.cd-agency/memory.json` for project-level terminology/voice decisions
7. **Config**: `.cd-agency.yaml` → environment variables → defaults (in that override order)

## File Naming Conventions

- Agent files: `kebab-case.md` in `content-design/`
- Python modules: `snake_case.py`
- Test files: `test_<module>.py` in `tests/`
- Workflow files: `kebab-case.yaml` in `workflows/`
- Preset files: `kebab-case.yaml` in `presets/`

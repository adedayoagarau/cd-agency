# CLI Overview

> Stability: Stable

CD Agency provides a comprehensive command-line interface built on
[Click](https://click.palletsprojects.com/).

## Entry Point

```bash
cd-agency [OPTIONS] COMMAND [ARGS]
```

The CLI is installed as `cd-agency` via the `[project.scripts]` entry point. It
can also be run as:

```bash
python -m runtime.cli [OPTIONS] COMMAND [ARGS]
```

## Global Options

| Option | Description |
| --- | --- |
| `--version` | Print version and exit |
| `--help` | Print help and exit |

## Command Groups

| Command | Description |
| --- | --- |
| [`agent`](cli-agent.md) | Run and manage content design agents |
| [`score`](cli-score.md) | Score and evaluate content quality |
| [`workflow`](cli-workflow.md) | Run multi-agent workflow pipelines |
| [`memory`](cli-memory.md) | Manage project-level memory |
| [`context`](cli-context.md) | Manage product context |
| [`export`](cli-export.md) | Export content in various formats |
| [`presets`](cli-presets.md) | List design system presets |
| [`stats`](cli-stats.md) | Show usage analytics |
| [`interactive`](cli-interactive.md) | Guided interactive session |

## Input Methods

Most commands accept text input through multiple methods:

```bash
# Inline text
cd-agency score readability -i "Your text here"

# From file
cd-agency score readability -f content.txt

# From stdin (pipe)
echo "Your text here" | cd-agency score readability
```

## Output Formats

Most commands support multiple output formats:

```bash
# Default: rich terminal output
cd-agency agent list

# JSON output
cd-agency agent list --json-output

# Markdown (scoring commands)
cd-agency score all -i "text" --markdown
```

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Error (validation, missing agent, API failure) |
| `2` | Usage error (invalid arguments) |

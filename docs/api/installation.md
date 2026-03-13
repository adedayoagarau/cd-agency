# Installation

> Stability: Stable

## Install from PyPI

```bash
pip install cd-agency
```

To include the REST API server (FastAPI + Uvicorn):

```bash
pip install cd-agency[api]
```

## Install from Source

```bash
git clone https://github.com/adedayoagarau/cd-agency.git
cd cd-agency
pip install -e .
```

## Install with Development Dependencies

```bash
pip install -e ".[dev]"
```

This adds `pytest` and `pytest-asyncio` for running the test suite.

## Verify Installation

```bash
cd-agency --version
# cd-agency, version 0.5.0
```

```bash
cd-agency agent list
# Shows all 17 agents in a table
```

## Dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| `anthropic` | >= 0.39.0 | Claude API client |
| `pyyaml` | >= 6.0 | YAML parsing for agents, workflows, presets |
| `pydantic` | >= 2.0 | Data validation |
| `rich` | >= 13.0 | Terminal formatting (tables, colors) |
| `click` | >= 8.1 | CLI framework |

## Set Up Your API Key

Agent execution requires an Anthropic API key. Scoring tools (readability,
lint, a11y) work without one.

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add it to your project config file:

```yaml
# .cd-agency.yaml
api_key: sk-ant-...
```

> **Security note:** The `.cd-agency.yaml` file is included in `.gitignore` by
> default to prevent accidental commits of API keys.

## Python Version Support

| Python | Status |
| --- | --- |
| 3.10 | Supported |
| 3.11 | Supported |
| 3.12 | Supported |
| 3.13+ | Untested |

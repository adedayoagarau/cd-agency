# CD Agency v0.5.0 Documentation

> AI-powered content design agents for UX writers, conversation designers, and product teams.

## About This Documentation

This is the complete API and usage reference for **CD Agency**, a Python toolkit
containing 17 specialized AI agents for UX writing, content design, and copy
optimization. It includes a CLI, scoring tools, auto-validation, content
versioning, multi-agent workflows, design system presets, a knowledge base of
52 curated content design resources, and a TUI studio.

**Stability Index:**

Throughout this documentation, stability indicators show the maturity of each
module:

| Stability   | Meaning                                      |
| ----------- | -------------------------------------------- |
| Stable      | API is locked. Breaking changes require major version bump. |
| Experimental | API may change between minor versions.       |

---

## Table of Contents

### Getting Started

- [About CD Agency](about.md)
- [Installation](installation.md)
- [Quick Start](quickstart.md)
- [Configuration](configuration.md)

### CLI Reference

- [CLI Overview](cli.md)
- [`agent` Commands](cli-agent.md)
- [`score` Commands](cli-score.md)
- [`workflow` Commands](cli-workflow.md)
- [`history` Commands](cli-history.md)
- [`memory` Commands](cli-memory.md)
- [`context` Commands](cli-context.md)
- [`export` Command](cli-export.md)
- [`presets` Command](cli-presets.md)
- [`stats` Command](cli-stats.md)
- [`interactive` Command](cli-interactive.md)

### Python API Reference

- [`runtime.agent` — Agent Model](agent.md)
- [`runtime.loader` — Agent Loader](loader.md)
- [`runtime.registry` — Agent Registry](registry.md)
- [`runtime.runner` — Agent Runner](runner.md)
- [`runtime.config` — Configuration](config.md)
- [`runtime.memory` — Project Memory](memory.md)
- [`runtime.workflow` — Workflow Engine](workflow.md)
- [`runtime.postprocess` — Auto-Validation](postprocess.md)
- [`runtime.versioning` — Content Versioning](versioning.md)

### Scoring Tools

- [`tools.scoring` — Readability Scorer](scoring.md)
- [`tools.linter` — Content Linter](linter.md)
- [`tools.a11y_checker` — Accessibility Checker](a11y.md)
- [`tools.voice_checker` — Voice Checker](voice.md)
- [`tools.report` — Scoring Reports](report.md)
- [`tools.export` — Export Formats](export.md)
- [`tools.analytics` — Usage Analytics](analytics.md)

### Agents

- [Agent Format Specification](agent-format.md)
- [All 17 Agents](agents.md)
- [Creating Custom Agents](custom-agents.md)

### Workflows

- [Workflow Format Specification](workflow-format.md)
- [Built-in Workflows](workflows.md)

### Design System Presets

- [Voice Presets](presets.md)

### Integrations

- [MCP, REST API, Figma, VS Code, GitHub Action](integrations.md)

### Guides

- [Scoring Your Content](guide-scoring.md)
- [Building Multi-Agent Pipelines](guide-workflows.md)
- [Integrating with CI/CD](guide-ci.md)

---

**License:** MIT
**Repository:** [github.com/adedayoagarau/cd-agency](https://github.com/adedayoagarau/cd-agency)
**Python:** 3.10+

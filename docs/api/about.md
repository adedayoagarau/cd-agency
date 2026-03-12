# About CD Agency

> Stability: Stable

CD Agency is a **Content Design Agency** — a collection of 16 specialized AI
agents for UX writing, content design, and copy optimization. It ships as a
Python package with a CLI, local scoring tools, multi-agent workflow pipelines,
and design system voice presets.

## What It Does

| Capability | Description |
| --- | --- |
| **16 AI Agents** | Specialized content design agents for errors, CTAs, onboarding, mobile, a11y, tone, notifications, search, legal/privacy, chatbot design, information architecture, and more. |
| **Scoring Tools** | Readability analysis (Flesch-Kincaid), content linting, WCAG accessibility checks, and brand voice scoring — all offline, no API key needed. |
| **Auto-Validation** | Post-processing pipeline that extracts content fragments from agent output and validates against UI constraints (character limits, platform conventions, a11y, localization expansion). |
| **Multi-Agent Workflows** | Chain agents in pipelines (e.g., "audit → tone check → a11y → polish"). Supports sequential and parallel execution. |
| **Content Versioning** | Before/after tracking for every agent run — browse, search, diff, and audit content changes over time. |
| **Design System Presets** | Pre-built voice profiles for Material Design, Shopify Polaris, Atlassian Design, and Apple HIG. |
| **Project Memory** | Persist terminology decisions, voice choices, and patterns across sessions. |
| **Export Formats** | JSON, CSV, Markdown, and XLIFF 1.2 for localization handoff. |
| **Usage Analytics** | Local-only tracking of agent usage, token consumption, and quality scores. |

## Architecture Overview

```
cd-agency/
├── runtime/           Core SDK
│   ├── agent.py       Agent model and data types
│   ├── loader.py      Markdown → Agent parser
│   ├── registry.py    Central agent lookup (slug, alias, tag)
│   ├── runner.py      Anthropic API execution with retry + auto-versioning
│   ├── config.py      Configuration (file + env + defaults)
│   ├── memory.py      Project-scoped memory store
│   ├── workflow.py     Multi-agent pipeline engine
│   ├── preflight.py   Context-aware clarifying questions before agent runs
│   ├── postprocess.py Auto-validation of agent output against UI constraints
│   ├── versioning.py  Content version history (before/after tracking)
│   └── cli.py         Click-based CLI entry point
│
├── tools/             Scoring & analysis (no API key needed)
│   ├── scoring.py     Readability metrics (Flesch-Kincaid)
│   ├── linter.py      Content lint rules (jargon, passive, CTA, inclusive, consistency mode)
│   ├── a11y_checker.py  WCAG text-level accessibility checks
│   ├── voice_checker.py Brand voice consistency (LLM or rule-based)
│   ├── report.py      Scoring report renderer (text, JSON, Markdown)
│   ├── export.py      Multi-format content export
│   └── analytics.py   Local usage analytics
│
├── api/               REST API (FastAPI)
│   ├── main.py        FastAPI app with CORS, health check
│   ├── deps.py        Dependencies: registry, runner, auth
│   ├── models.py      Pydantic request/response schemas
│   └── routers/       Endpoint modules (agents, scoring, presets, validate, history)
│
├── mcp/               Model Context Protocol server (stdio)
│   ├── server.py      JSON-RPC server with 12 tools and 3 resources
│   └── README.md      MCP integration guide
│
├── content-design/    16 agent definitions (.md with YAML frontmatter)
├── workflows/         5 workflow pipelines (.yaml)
├── presets/           4 design system voice profiles (.yaml)
└── tests/             490+ unit and integration tests (pytest)
```

## Design Principles

1. **Agents are data, not code.** Agent definitions are Markdown files with YAML
   frontmatter. No Python needed to create or modify agents.

2. **Scoring is free.** Readability, linting, and accessibility checks run
   entirely offline. Only agent execution and LLM voice checking need an API key.

3. **Memory persists.** Terminology decisions and voice preferences survive
   across sessions via a JSON-backed project memory store.

4. **Pipelines compose.** Multi-agent workflows chain agents with data flow
   between steps (`$input.field`, `$steps.previous.content`).

5. **Everything exports.** Reports render as text, JSON, or Markdown. Content
   exports as JSON, CSV, Markdown tables, or XLIFF 1.2.

## Requirements

- Python 3.10 or later
- `ANTHROPIC_API_KEY` environment variable (for agent execution only)
- Dependencies: `anthropic`, `pyyaml`, `pydantic`, `rich`, `click`

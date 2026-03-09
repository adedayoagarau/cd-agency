# Content Design Agency

A complete AI agency specializing in Content Design. 15 specialized agents for UX writing, microcopy, content strategy, and conversation design — each with structured inputs/outputs, system prompts, and few-shot examples ready for integration.

Each agent is:

- **Specialized**: Deep expertise in specific content design domains
- **Machine-Parseable**: Structured YAML frontmatter with typed inputs/outputs
- **Prompt-Engineered**: Real system prompts with few-shot examples, not personality fluff
- **Composable**: Agents reference each other via `related_agents` for multi-step workflows

## Quick Start

1. **Pick an agent** from the table below (or use the [decision tree](./docs/WHEN_TO_USE.md))
2. **Copy the agent file** to your AI system
3. **Use the System Prompt section** as your system message and the Few-Shot Examples for calibration

Not sure which agent to use? Start with the [Content Designer Generalist](./content-design/content-designer-generalist.md) — it will recommend specialists.

## Not Sure Which Agent? → [Decision Tree](./docs/WHEN_TO_USE.md)

The decision tree maps every common content design task to the right agent, including multi-agent handoff patterns.

## Content Design Agents

| Agent | Specialty | When to Use |
| :--- | :--- | :--- |
| [Content Designer Generalist](./content-design/content-designer-generalist.md) | UX writing, microcopy, content strategy | General content tasks, initial drafts, not sure where to start |
| [Conversational AI Designer](./content-design/conversational-ai-designer.md) | Chatbot scripts, voice UIs, dialog flows | Designing dialogue for chatbots, IVRs, or voice assistants |
| [Accessibility Content Auditor](./content-design/accessibility-content-auditor.md) | WCAG compliance, inclusive language | Auditing content for accessibility, inclusive language |
| [Microcopy Review Agent](./content-design/microcopy-review-agent.md) | Microcopy refinement, UX text optimization | Reviewing button labels, tooltips, form fields for clarity |
| [Tone Evaluation Agent](./content-design/tone-evaluation-agent.md) | Tone analysis, brand voice alignment | Assessing and refining emotional register and brand voice |
| [Onboarding Flow Designer](./content-design/onboarding-flow-designer.md) | Onboarding experiences, user activation | Crafting flows that get users to their first "aha" moment |
| [Technical Documentation Writer](./content-design/technical-documentation-writer.md) | API docs, SDK guides, technical content | Creating developer documentation with code examples |
| [CTA Optimization Specialist](./content-design/cta-optimization-specialist.md) | Conversion CTAs, persuasive microcopy | Designing calls-to-action backed by psychology principles |
| [Error Message Architect](./content-design/error-message-architect.md) | Human-centered error messages | Designing error messages that guide users to resolution |
| [Mobile UX Writer](./content-design/mobile-ux-writer.md) | Mobile microcopy, app content | Concise content optimized for mobile constraints |
| [Localization Content Strategist](./content-design/localization-content-strategist.md) | i18n, cultural adaptation | Preparing content for global audiences and translation |
| [Notification Content Designer](./content-design/notification-content-designer.md) | Push, in-app, email notifications | Crafting notifications that earn their interruption |
| [Privacy & Legal Content Simplifier](./content-design/privacy-legal-content-simplifier.md) | Legal clarity, compliance content | Translating legal jargon into plain language |
| [Empty State & Placeholder Specialist](./content-design/empty-state-placeholder-specialist.md) | Empty states, loading messages | Turning blank screens into guidance opportunities |
| [Search Experience Writer](./content-design/search-experience-writer.md) | Search UI, no-results, filters | Optimizing search placeholders, results, and recovery |

## Agent File Structure

Every agent file includes:

```yaml
# YAML Frontmatter
name: Agent Name
description: One-line description
version: "1.0.0"
difficulty_level: beginner | intermediate | advanced
tags: [searchable, keywords]
inputs:
  - name: field_name
    type: string
    required: true
    description: What this input is
outputs:
  - name: field_name
    type: string
    description: What this output contains
related_agents:
  - other-agent-name
```

Plus markdown sections:
- **System Prompt** — Drop-in system message for your LLM
- **Few-Shot Examples** — Input/output pairs showing ideal behavior
- **Core Mission** — What the agent does
- **Critical Rules** — Constraints and principles
- **Technical Deliverables** — What it produces
- **Workflow Process** — Step-by-step interaction flow
- **Success Metrics** — How to measure quality

## Runtime SDK

Agents are executable via the Python runtime. Install and use programmatically or from the CLI.

### Installation

```bash
pip install -e .
```

Requires `ANTHROPIC_API_KEY` environment variable (see `.env.example`).

### CLI Usage

```bash
# List all agents
cd-agency agent list

# Filter by tag or difficulty
cd-agency agent list --tag mobile
cd-agency agent list --difficulty beginner

# Get agent details (supports aliases: "error", "cta", "a11y", "tone", etc.)
cd-agency agent info error

# Run an agent
cd-agency agent run error-message-architect -i "API returns 503 during checkout"
cd-agency agent run microcopy -i "Click here to proceed" -F ui_context="checkout button"

# Pipe input
echo "Submit" | cd-agency agent run cta

# JSON output
cd-agency agent run tone -i "Your request has been denied." --json-output
```

### Python SDK

```python
from runtime import load_agent, AgentRegistry, Config
from runtime.runner import AgentRunner

# Load a single agent
agent = load_agent(Path("content-design/error-message-architect.md"))

# Or use the registry (supports aliases)
registry = AgentRegistry.from_directory(Path("content-design"))
agent = registry.get("error")  # alias for error-message-architect

# Run the agent
config = Config.from_env()
runner = AgentRunner(config)
result = runner.run(agent, {
    "error_scenario": "Payment gateway timeout",
    "severity": "critical",
    "target_audience": "non-technical shopper",
})

print(result.content)       # The agent's response
print(result.input_tokens)  # Token usage
print(result.latency_ms)    # Response time
```

## Project Structure

```
cd-agency/
├── content-design/     # 15 agent definitions + template
├── runtime/            # Core SDK
│   ├── agent.py        # Agent model
│   ├── loader.py       # Markdown parser
│   ├── registry.py     # Agent lookup with fuzzy matching
│   ├── runner.py       # Anthropic API execution
│   ├── cli.py          # CLI (agents, workflows, scoring, memory, stats)
│   ├── config.py       # Config file + env var management
│   ├── memory.py       # Project-level memory store
│   └── agent_builder.py # Custom agent wizard
├── tools/              # Scoring & evaluation tools
│   ├── scoring.py      # Readability (Flesch-Kincaid)
│   ├── linter.py       # Content lint (7+ rules)
│   ├── a11y_checker.py # WCAG accessibility
│   ├── voice_checker.py # Brand voice consistency
│   ├── report.py       # Report generation
│   ├── export.py       # Export (JSON, CSV, Markdown, XLIFF)
│   └── analytics.py    # Usage tracking (local, privacy-first)
├── presets/            # Design system voice profiles
│   ├── material-design.yaml
│   ├── shopify-polaris.yaml
│   ├── atlassian-design.yaml
│   └── apple-hig.yaml
├── tests/              # 226 unit tests
├── docs/               # Specs and guides
│   ├── WHEN_TO_USE.md
│   ├── figma-plugin-spec.md
│   └── vscode-extension-spec.md
├── .github/            # GitHub Action + issue templates
├── examples/           # 17 before/after case studies
├── workflows/          # 5 multi-agent pipeline definitions
├── IMPLEMENTATION_PLAN.md
├── ROADMAP.md
└── README.md
```

## See It In Action

Every agent ships with before/after case studies showing measurable improvements. Here are highlights:

### Individual Agent Examples

| Agent | Case Study | Key Result |
|-------|-----------|------------|
| Error Message Architect | [E-commerce 503 error](./examples/error-message-architect-01.md) | Generic "Something went wrong" → empathetic message with 3 resolution steps |
| Microcopy Review | [Registration form labels](./examples/microcopy-review-02.md) | 319 chars → 43 chars (87% reduction), readability Grade 14 → Grade 3 |
| CTA Optimization | [SaaS pricing page](./examples/cta-optimization-01.md) | "Submit" → "Start my free trial" with 5 psychology-backed variations |
| Onboarding Flow Designer | [Mobile banking first login](./examples/onboarding-flow-designer-02.md) | 7 screens → 2 screens, 3 min → 45 sec to reach account |
| Accessibility Auditor | [Dashboard visualizations](./examples/accessibility-content-auditor-02.md) | 5 WCAG violations → 0, full color-blind + keyboard support |

### Multi-Agent Workflow Examples

| Workflow | Case Study | What Happened |
|----------|-----------|---------------|
| Content Audit (4 agents) | [Healthcare appointment page](./examples/workflow-content-audit-01.md) | 4-agent pipeline: structural fix → tone calibration → a11y audit → microcopy polish. Readability Grade 14 → Grade 5 |
| Launch Content Package (4 agents) | [Feature launch — Team Insights](./examples/workflow-launch-content-package-01.md) | 3 agents in parallel (onboarding + CTAs + empty states) → generalist consolidation. 10 content pieces, 282 words, terminology-consistent |

All 17 case studies follow a [consistent template](./examples/TEMPLATE.md): Context → Before → After → What Changed & Why → Measurable Difference.

Browse all examples in the [`examples/`](./examples/) directory.

## Workflows

Chain agents into multi-step pipelines using YAML workflow definitions:

```bash
# List available workflows
cd-agency workflow list

# Run a content audit pipeline
cd-agency workflow run content-audit --field content="Your button text here"

# Run a launch content package (parallel agents + consolidation)
cd-agency workflow run launch-content-package --field feature_name="Team Insights"
```

5 pre-built workflows in [`workflows/`](./workflows/):
- **Content Audit** — Generalist → Tone → Accessibility → Microcopy (sequential)
- **Error Message Pipeline** — Error Architect → Tone → A11y → Mobile (sequential)
- **Launch Content Package** — Onboarding + CTA + Empty State (parallel) → Generalist (consolidation)
- **Localization Prep** — L10n → Generalist simplification → A11y check (sequential)
- **Notification Suite** — Notifications → Mobile → Tone → CTA (sequential)

## Scoring & Evaluation

Score content quality from the CLI — readability, lint rules, accessibility, and brand voice consistency.

```bash
# Readability metrics (Flesch-Kincaid, reading ease, complexity)
cd-agency score readability -i "Your content here"

# Content lint (passive voice, jargon, inclusive language, char limits)
cd-agency score lint -i "Click here to submit" --type button

# Accessibility check (WCAG text compliance, reading level, ALL CAPS, link text)
cd-agency score a11y -i "CLICK HERE for more info"

# Brand voice consistency (requires a voice guide YAML)
cd-agency score voice -i "Your content" --guide brand-voice.yaml --no-llm

# Run all checks at once
cd-agency score all -i "Your content" --type cta --json-output

# Compare before/after readability
cd-agency score readability -i "Simple version" --compare "Complex original version"
```

**4 scoring tools** in [`tools/`](./tools/):
- **Readability Scorer** — Flesch-Kincaid grade, Flesch Reading Ease, complexity index, reading time
- **Content Linter** — 7+ rules: action verbs, error actionability, passive voice, char limits, jargon, inclusive language, terminology consistency
- **Accessibility Checker** — WCAG text-level: reading level, sentence length, ALL CAPS, emoji overuse, link text, alt text
- **Voice Checker** — LLM-powered or rule-based brand voice consistency scoring (1-10 scale)

Output formats: plain text (terminal), JSON, and Markdown.

## Design System Presets

Pre-configured brand voice profiles for popular design systems:

```bash
# Check content against Material Design writing guidelines
cd-agency score voice -i "Click here to submit" --guide presets/material-design.yaml --no-llm

# List available presets
cd-agency presets
```

4 presets included in [`presets/`](./presets/):
- **Material Design** — Google's writing guidelines (sentence case, "you", present tense)
- **Shopify Polaris** — Merchant-focused, grade 7 reading level, verb+noun buttons
- **Atlassian Design** — Bold, optimistic, team-oriented, sentence case everywhere
- **Apple HIG** — Friendly, title case buttons, "tap" not "click" on iOS

Each preset includes tone descriptors, do/don't rules, sample content, character limits, and terminology glossary.

## Interactive Mode

New to the agency? The guided interactive mode walks you through:

```bash
cd-agency interactive
```

1. Asks "What are you working on?" → suggests the right agent
2. Walks through required inputs with prompts
3. Shows agent output with optional quality scoring
4. Offers handoff to related agents

## Export Formats

Export before/after content in formats compatible with CMS, translation, and design tools:

```bash
# JSON (CMS import)
cd-agency export -i "Submit" -o "Start free trial" --format json

# CSV (spreadsheet review)
cd-agency export -i "Submit" -o "Start free trial" --format csv

# XLIFF (translation tools)
cd-agency export -i "Submit" -o "Start free trial" --format xliff

# Markdown (documentation)
cd-agency export -i "Submit" -o "Start free trial" --format markdown
```

## Integrations

### GitHub Action

Lint content in pull requests automatically:

```yaml
- uses: adedayoagarau/cd-agency/.github/actions/content-lint@main
  with:
    file_patterns: "src/locales/**/*.json,src/components/**/*.tsx"
    content_type: general
    fail_on_error: true
```

See [full usage example](./examples/github-action-usage.yml).

### Figma Plugin (Spec)

Select text layers → run agents → apply suggestions. [View spec](./docs/figma-plugin-spec.md).

### VS Code Extension (Spec)

Inline content lint, command palette agents, sidebar scoring panel. [View spec](./docs/vscode-extension-spec.md).

## Config File

Create a `.cd-agency.yaml` in your project root to set defaults:

```yaml
model: claude-sonnet-4-20250514
agents_dir: content-design
default_preset: material-design
brand_voice_guide: presets/material-design.yaml
output_format: text  # text, json, markdown
```

Environment variables override config file values.

## Custom Agent Builder

Create your own agents with the interactive wizard:

```bash
cd-agency agent create
```

Or copy `content-design/agent-template.md` and fill in the sections.

## Project Memory

Agents remember decisions across sessions:

```bash
# Store terminology decisions
cd-agency memory add "app_name" "workspace" --category terminology
cd-agency memory add "tone" "friendly but professional" --category voice

# View stored memory
cd-agency memory show

# Memory gets injected into agent context automatically
```

## Usage Analytics

Local, privacy-first usage tracking:

```bash
cd-agency stats                # Dashboard
cd-agency stats --json-output  # JSON export
cd-agency stats --csv-output   # CSV export
```

## Use with AI Coding Tools

CD Agency ships with configuration files for all major AI coding tools:

| Tool | Config File | What It Does |
|------|-------------|-------------|
| **Claude Code** | `CLAUDE.md` | Project context, architecture, conventions |
| **Cursor** | `.cursorrules` | Codebase rules and patterns |
| **Windsurf** | `.windsurfrules` | Same format as Cursor |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Copilot workspace context |
| **Replit** | `.replit` | Run config, entrypoint, environment |
| **Bolt.new** | `.bolt` | Project config for Bolt |
| **Codex / Others** | `AGENTS.md` | Universal agent instructions |

All tools get:
- Full project architecture overview
- Key commands (`pytest`, `cd-agency agent run`, etc.)
- Conventions (Python 3.10+, type hints, dataclasses)
- File naming and module patterns

## Docker

```bash
docker build -t cd-agency .
docker run cd-agency agent list
docker run -e ANTHROPIC_API_KEY=sk-... cd-agency agent run error -i "timeout"
```

## Integration with `content-design-prompt-library`

This agency works alongside the [content-design-prompt-library](https://github.com/adedayoagarau/content-design-prompt-library). Use prompts from the library as input to the agents here for structured, high-quality content generation.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). You can add:
- New specialist agents (`cd-agency agent create` or copy the template)
- Before/after case studies in `/examples`
- Multi-agent workflow definitions in `/workflows`
- Design system presets in `/presets`
- Lint rules in `tools/linter.py`

## License

MIT License

# Content Design Agency

A complete AI agency specializing in Content Design. 15 specialized agents for UX writing, microcopy, content strategy, and conversation design — each with structured inputs/outputs, system prompts, and few-shot examples ready for integration.

Built on the principles of [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents). Each agent is:

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
├── content-design/     # 15 agent definition files
├── runtime/            # Python SDK — loader, runner, registry, CLI
│   ├── agent.py        # Core Agent model
│   ├── loader.py       # Parses .md files into Agent objects
│   ├── registry.py     # Agent lookup with aliases and filtering
│   ├── runner.py       # Executes agents via Anthropic API
│   └── cli.py          # CLI entry point
├── tests/              # 45 unit tests
├── docs/               # Decision tree and documentation
│   └── WHEN_TO_USE.md  # Agent selection guide
├── examples/           # Before/after case studies (coming)
├── workflows/          # Multi-agent pipeline definitions (coming)
├── tools/              # Evaluation & scoring (coming)
├── IMPLEMENTATION_PLAN.md
├── ROADMAP.md
└── README.md
```

## Roadmap

See [ROADMAP.md](./ROADMAP.md) for the full plan. Next up:

- **Multi-agent workflows** — Chain agents into pipelines (Content Audit, Launch Package, etc.)
- **Before/after examples** — Real case studies proving quality improvements
- **Scoring tools** — Automated readability, accessibility, and brand voice scoring

## Integration with `content-design-prompt-library`

This agency works alongside the [content-design-prompt-library](https://github.com/adedayoagarau/content-design-prompt-library). Use prompts from the library as input to the agents here for structured, high-quality content generation.

## Contributing

We welcome contributions! You can add:
- New specialist agents (use any existing agent as a template)
- Before/after case studies in `/examples`
- Multi-agent workflow definitions in `/workflows`
- Design system presets

## License

MIT License

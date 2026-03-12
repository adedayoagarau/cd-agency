# `agent` Commands

> Stability: Stable

Manage and run content design agents.

```bash
cd-agency agent COMMAND [ARGS]
```

## `agent list`

List all available agents.

```bash
cd-agency agent list [OPTIONS]
```

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--tag TAG` | string | Filter agents by tag (e.g., `errors`, `a11y`, `mobile`) |
| `--difficulty LEVEL` | choice | Filter by difficulty: `beginner`, `intermediate`, `advanced` |
| `--json-output` | flag | Output as JSON array |

**Examples:**

```bash
# List all agents
cd-agency agent list

# Filter by tag
cd-agency agent list --tag errors

# Filter by difficulty
cd-agency agent list --difficulty advanced

# JSON output
cd-agency agent list --json-output
```

**JSON output structure:**

```json
[
  {
    "name": "Error Message Architect",
    "slug": "error-message-architect",
    "description": "Designs human-centered, helpful error messages...",
    "tags": ["errors", "error-messages", "recovery"],
    "difficulty": "intermediate"
  }
]
```

---

## `agent info`

Show detailed information about a single agent.

```bash
cd-agency agent info NAME
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `NAME` | Agent slug, alias, or full name |

The command shows:

- Agent name and version
- Description
- Required and optional inputs (name, type, description)
- Output fields
- Related agents
- Tags and difficulty level
- Source file path

**Example:**

```bash
cd-agency agent info error
```

```
Error Message Architect (v1.0.0)
Designs human-centered, helpful error messages that guide users to resolution.

Required Inputs:
  - error_scenario (string): The error condition

Optional Inputs:
  - technical_details (string): Error codes, API responses...
  - severity (string): critical | warning | info
  - target_audience (string): User technical level
  - brand_guidelines (string): Brand voice guidelines

Outputs:
  - user_message (string): The user-facing error message
  - resolution_steps (string[]): Steps to fix the issue
  - developer_note (string): Technical companion note
  - prevention_tip (string): Guidance to prevent this error

Related Agents: content-designer-generalist, accessibility-content-auditor...
Tags: errors, error-messages, recovery, troubleshooting, validation
Difficulty: intermediate
```

---

## `agent run`

Run an agent with the given input. Requires `ANTHROPIC_API_KEY`.

```bash
cd-agency agent run NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `NAME` | Agent slug, alias, or full name |

**Options:**

| Option | Short | Type | Description |
| --- | --- | --- | --- |
| `--input` | `-i` | string | Inline text (maps to first required field) |
| `--file` | `-f` | path | Read input from file |
| `--field` | `-F` | key=value | Set a specific input field (repeatable) |
| `--model` | `-m` | string | Override the default model |
| `--validate` | `-V` | flag | Auto-validate output against UI constraints |
| `--platform` | `-p` | string | Target platform for validation (`ios`, `android`, `web`) |
| `--json-output` | | flag | Output as JSON |

**Examples:**

```bash
# Simple input (maps to first required field)
cd-agency agent run error -i "File upload exceeds 10MB limit"

# Multiple fields
cd-agency agent run error \
  -F "error_scenario=File upload exceeds 10MB" \
  -F "severity=warning" \
  -F "target_audience=non-technical consumer"

# Override model
cd-agency agent run error -i "..." --model claude-opus-4-20250514

# JSON output with token usage
cd-agency agent run error -i "..." --json-output

# Read input from file
cd-agency agent run generalist -f content.txt

# Pipe from stdin
echo "Submit your information" | cd-agency agent run microcopy

# Auto-validate output against UI constraints
cd-agency agent run error -i "Payment failed" --validate

# Validate for a specific platform
cd-agency agent run mobile -i "Saved" --validate --platform ios
```

**JSON output structure:**

```json
{
  "agent": "Error Message Architect",
  "model": "claude-sonnet-4-20250514",
  "content": "...",
  "input_tokens": 1234,
  "output_tokens": 567,
  "latency_ms": 2340.5
}
```

---

## `agent create`

Create a new custom agent with an interactive wizard.

```bash
cd-agency agent create
```

Launches a guided prompt to define:

- Agent name and description
- Input and output fields
- Tags and difficulty level
- System prompt content

The agent is saved as a `.md` file in the configured agents directory.

---

## `agent import`

Import an agent from an external file.

```bash
cd-agency agent import SOURCE
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `SOURCE` | Path to a `.md` agent definition file |

---

## Agent Aliases

Agents can be referenced by slug, full name, or alias:

| Alias | Agent |
| --- | --- |
| `generalist`, `general` | content-designer-generalist |
| `error`, `errors` | error-message-architect |
| `microcopy` | microcopy-review-agent |
| `tone`, `voice` | tone-evaluation-agent |
| `a11y`, `accessibility`, `wcag` | accessibility-content-auditor |
| `cta` | cta-optimization-specialist |
| `onboarding` | onboarding-flow-designer |
| `docs`, `tech-docs` | technical-documentation-writer |
| `ia`, `architecture` | information-architect |
| `mobile` | mobile-ux-writer |
| `l10n`, `localization`, `i18n` | localization-content-strategist |
| `notifications`, `notify`, `push` | notification-content-designer |
| `privacy`, `legal` | privacy-legal-content-simplifier |
| `empty`, `placeholder` | empty-state-placeholder-specialist |
| `search` | search-experience-writer |
| `chatbot`, `conversation` | conversational-ai-designer |

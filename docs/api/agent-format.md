# Agent Format Specification

> Stability: Stable

Agents are defined as Markdown files with YAML frontmatter. No Python code is
needed to create or modify agents.

## File Structure

```
content-design/
├── error-message-architect.md
├── content-designer-generalist.md
├── ...
└── agent-template.md
```

The filename (without `.md`) becomes the agent's **slug** — the primary
identifier used in CLI commands and the registry.

## Template

```markdown
---
name: Your Agent Name
description: A one-line description of what this agent does.
color: "#4CAF50"
version: "1.0.0"
difficulty_level: intermediate    # beginner | intermediate | advanced
tags: ["content-design", "your-tag"]
inputs:
  - name: primary_input
    type: string
    required: true
    description: "What this input expects"
  - name: optional_input
    type: string
    required: false
    description: "Additional context"
outputs:
  - name: result
    type: string
    description: "What the agent returns"
related_agents:
  - content-designer-generalist
  - tone-evaluation-agent
---

### System Prompt

You are a [role description]. Your job is to...

### Critical Rules

1. Rule one
2. Rule two
3. Rule three

### Few-Shot Examples

**Input:** [example input]

**Output:** [example output]

---

**Input:** [another example]

**Output:** [another output]
```

## YAML Frontmatter Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Human-readable agent name |
| `description` | string | yes | One-line description |
| `color` | string | no | Hex color for UI display |
| `version` | string | no | Semver version (default: `"1.0.0"`) |
| `difficulty_level` | string | no | `beginner`, `intermediate`, or `advanced` |
| `tags` | list[string] | no | Searchable tags |
| `inputs` | list[object] | yes | Input field definitions |
| `outputs` | list[object] | no | Output field definitions |
| `related_agents` | list[string] | no | Slugs of related agents |

### Input Object

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Field name (snake_case) |
| `type` | string | no | Expected type (default: `"string"`) |
| `required` | boolean | no | Whether the field is mandatory (default: `true`) |
| `description` | string | no | Human-readable description |

### Output Object

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Field name |
| `type` | string | no | Expected type |
| `description` | string | no | Human-readable description |

## Markdown Sections

The body after the frontmatter is parsed into sections by `###` headers:

| Section | Purpose |
| --- | --- |
| `### System Prompt` | The main system prompt sent to Claude |
| `### Critical Rules` | Hard constraints the agent must follow |
| `### Few-Shot Examples` | Example input/output pairs for the agent |
| `### Core Mission` | High-level purpose statement |
| `### Technical Deliverables` | Specific output format requirements |
| `### Workflow Process` | Step-by-step process the agent follows |
| `### Success Metrics` | How to evaluate agent output quality |

Only `System Prompt` and `Few-Shot Examples` are checked for completeness in
tests. Other sections are optional.

## System Message Composition

When an agent is run, the system message is composed from:

1. `system_prompt` section content
2. `few_shot_examples` section content
3. `critical_rules` (wrapped in `## Critical Rules`)

Sections are joined with `---` separators.

## Creating a New Agent

```bash
# Interactive wizard
cd-agency agent create

# Or manually: create a .md file in content-design/
```

After creating the file, the agent is automatically available in the CLI and
registry.

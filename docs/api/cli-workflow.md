# `workflow` Commands

> Stability: Stable

Run multi-agent workflow pipelines.

```bash
cd-agency workflow COMMAND [ARGS]
```

## `workflow list`

List all available workflows.

```bash
cd-agency workflow list [OPTIONS]
```

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |

**Example:**

```bash
cd-agency workflow list
```

```
                         Workflows (5)
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Workflow               ┃ Description                 ┃ Steps ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ content-audit          │ Comprehensive content audit  │   4   │
│ error-message-pipeline │ End-to-end error creation    │   4   │
│ launch-content-package │ Product launch content       │   4   │
│ localization-prep      │ Prepare for global deploy    │   3   │
│ notification-suite     │ Multi-channel notifications  │   4   │
└────────────────────────┴─────────────────────────────┴───────┘
```

---

## `workflow info`

Show detailed information about a workflow, including steps and input mapping.

```bash
cd-agency workflow info NAME
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `NAME` | Workflow slug or name |

**Example:**

```bash
cd-agency workflow info content-audit
```

```
Full Content Audit
Comprehensive content quality audit. The Generalist scans for overall issues,
then the Tone Evaluator checks voice, the Accessibility Auditor flags a11y
issues, and the Microcopy Reviewer polishes the final output.

Steps:
  1. generalist_scan → agent: generalist
     content_or_context: $input.content
     brand_guidelines: $input.brand_guidelines
  2. tone_check → agent: tone
     content: $input.content
     target_tone: $input.target_tone
  3. accessibility_audit → agent: a11y
     content: $input.content
  4. microcopy_polish → agent: microcopy
     microcopy: $input.content
```

---

## `workflow run`

Execute a multi-agent workflow pipeline. Requires `ANTHROPIC_API_KEY`.

```bash
cd-agency workflow run NAME [OPTIONS]
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `NAME` | Workflow slug or name |

**Options:**

| Option | Short | Type | Description |
| --- | --- | --- | --- |
| `--field` | `-F` | key=value | Set input field (repeatable) |
| `--json-output` | | flag | Output as JSON |

**Example:**

```bash
cd-agency workflow run content-audit \
  -F "content=Welcome to our app! Click here to get started." \
  -F "brand_guidelines=Friendly and professional" \
  -F "target_audience=New users"
```

**JSON output structure:**

```json
{
  "workflow": "Full Content Audit",
  "steps": [
    {
      "step": "generalist_scan",
      "agent": "Content Designer Generalist",
      "skipped": false,
      "error": null,
      "content": "..."
    }
  ],
  "total_tokens": { "input": 5000, "output": 2000, "total": 7000 },
  "total_latency_ms": 12500.3
}
```

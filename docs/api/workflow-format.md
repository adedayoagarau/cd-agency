# Workflow Format Specification

> Stability: Stable

Workflows are defined as YAML files in the `workflows/` directory.

## File Structure

```yaml
name: Workflow Display Name
description: >
  Multi-line description of what the workflow does and how
  the agents work together.

steps:
  - name: step_identifier
    agent: agent-slug-or-alias
    input_map:
      agent_field: "$input.workflow_field"
      another_field: "$steps.previous_step.content"
    output_key: step_result_key

  - name: second_step
    agent: another-agent
    input_map:
      content: "$steps.step_identifier.content"
    output_key: second_result
```

## Fields

### Top-Level

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Human-readable workflow name |
| `description` | string | no | Multi-line description |
| `steps` | list | yes | Ordered list of workflow steps |

### Step Fields

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `name` | string | yes | Step identifier (used in output references) |
| `agent` | string | yes | Agent slug or alias |
| `input_map` | dict | yes | Maps agent input fields to data sources |
| `output_key` | string | no | Key for storing output (defaults to `name`) |
| `parallel_group` | string | no | Steps with same group run concurrently |
| `condition` | string | no | Python expression for conditional execution |

## Input Map References

| Syntax | Resolves To |
| --- | --- |
| `$input.<field>` | Workflow input field provided at runtime |
| `$steps.<step_name>.content` | Text output from a previous step |
| `$steps.<step_name>.<field>` | Other field from a previous step's output |
| `"literal text"` | Used as-is |

## Parallel Execution

Steps with the same `parallel_group` value run concurrently:

```yaml
steps:
  - name: tone_check
    agent: tone
    parallel_group: "quality_checks"
    input_map:
      content: "$input.content"

  - name: a11y_check
    agent: a11y
    parallel_group: "quality_checks"
    input_map:
      content: "$input.content"
```

## Conditional Steps

Use `condition` to conditionally skip steps:

```yaml
steps:
  - name: mobile_check
    agent: mobile
    condition: "input.platform == 'mobile'"
    input_map:
      content: "$input.content"
```

Conditions are evaluated safely using AST parsing. Allowed: comparisons,
boolean logic, attribute access, literals. No function calls or imports.

## Example: Error Message Pipeline

```yaml
name: Error Message Pipeline
description: >
  End-to-end error message creation. The Error Architect drafts,
  the Tone Evaluator checks voice, the A11y Auditor ensures
  accessibility, and the Microcopy Reviewer polishes.

steps:
  - name: draft
    agent: error
    input_map:
      error_scenario: "$input.error_scenario"
      severity: "$input.severity"
      target_audience: "$input.target_audience"
    output_key: draft

  - name: tone_review
    agent: tone
    input_map:
      content: "$steps.draft.content"
      target_tone: "$input.target_tone"
    output_key: tone_result

  - name: a11y_check
    agent: a11y
    input_map:
      content: "$steps.draft.content"
    output_key: a11y_result

  - name: polish
    agent: microcopy
    input_map:
      microcopy: "$steps.draft.content"
      brand_voice: "$input.brand_guidelines"
    output_key: final
```

# Guide: Building Multi-Agent Pipelines

> Chain agents together for comprehensive content workflows.

## Why Workflows?

A single agent does one thing well. A workflow chains multiple agents for
end-to-end content production:

```
Error scenario → [Error Architect] → [Tone Check] → [A11y Audit] → [Polish] → Final copy
```

Each step receives the output of previous steps plus the original input.

## Running a Built-in Workflow

```bash
cd-agency workflow list
cd-agency workflow info content-audit
cd-agency workflow run content-audit \
  -F "content=Welcome! Click here to get started." \
  -F "brand_guidelines=Professional but friendly"
```

## Creating a Custom Workflow

### 1. Create the YAML File

```bash
touch workflows/my-workflow.yaml
```

### 2. Define Steps

```yaml
name: My Custom Workflow
description: >
  Description of what the workflow accomplishes.

steps:
  - name: draft
    agent: generalist
    input_map:
      content_or_context: "$input.content"
      brand_guidelines: "$input.guidelines"
    output_key: draft_result

  - name: review
    agent: microcopy
    input_map:
      microcopy: "$steps.draft_result.content"
      brand_voice: "$input.guidelines"
    output_key: review_result
```

### 3. Run It

```bash
cd-agency workflow run my-workflow \
  -F "content=Your content here" \
  -F "guidelines=Keep it short"
```

## Data Flow Patterns

### Workflow Input → Agent

```yaml
input_map:
  error_scenario: "$input.error_scenario"  # From workflow input
```

### Previous Step → Agent

```yaml
input_map:
  content: "$steps.draft.content"  # Output of "draft" step
```

### Literal Values

```yaml
input_map:
  severity: "warning"  # Hardcoded value
```

### Mixed References

```yaml
input_map:
  content: "$input.content"           # From workflow input
  previous: "$steps.draft.content"    # From previous step
  tone: "professional"                # Literal
```

## Parallel Execution

Steps in the same `parallel_group` run concurrently:

```yaml
steps:
  - name: draft
    agent: error
    input_map:
      error_scenario: "$input.scenario"

  # These two run at the same time
  - name: tone_check
    agent: tone
    parallel_group: "reviews"
    input_map:
      content: "$steps.draft.content"

  - name: a11y_check
    agent: a11y
    parallel_group: "reviews"
    input_map:
      content: "$steps.draft.content"

  - name: polish
    agent: microcopy
    input_map:
      microcopy: "$steps.draft.content"
```

## Conditional Steps

Skip steps based on input values:

```yaml
steps:
  - name: mobile_review
    agent: mobile
    condition: "input.platform == 'mobile'"
    input_map:
      content: "$input.content"
```

## Python API

```python
from pathlib import Path
from runtime.registry import AgentRegistry
from runtime.workflow import WorkflowEngine, load_workflow

registry = AgentRegistry.from_directory(Path("content-design"))
engine = WorkflowEngine(
    registry=registry,
    on_step_start=lambda name, agent: print(f"  Running {name}..."),
    on_step_complete=lambda name, result: print(f"  Done: {name}"),
)

workflow = load_workflow(Path("workflows/content-audit.yaml"))
result = engine.run(workflow, {
    "content": "Welcome! Click here to get started.",
    "brand_guidelines": "Professional but friendly",
})

# Access individual step results
for step in result.step_results:
    print(f"\n--- {step.step_name} ({step.agent_name}) ---")
    print(step.output.content[:200])

# Or just the final output
print(result.final_output)
print(f"Tokens: {result.total_tokens}")
```

## Tips

1. **Start simple.** A 2-step workflow is better than no workflow.
2. **Use parallel groups** for independent checks (tone + a11y can run at the
   same time).
3. **End with polish.** The Microcopy Review Agent is a good final step.
4. **Check agent resolution.** Run `cd-agency workflow info` to verify all
   agents resolve correctly.
5. **Test incrementally.** Add one step at a time and verify data flow.

# `runtime.workflow` — Workflow Engine

> Stability: Stable

```python
from runtime.workflow import (
    Workflow, WorkflowStep, WorkflowResult, StepResult,
    WorkflowEngine, load_workflow, load_workflows_from_directory,
)
```

Multi-agent workflow pipelines — chain multiple agents sequentially or in
parallel with data flow between steps.

## Class: `WorkflowStep`

A single step in a workflow pipeline.

```python
@dataclass
class WorkflowStep:
    name: str
    agent: str                       # Agent slug or alias
    input_map: dict[str, str]        # Field name → source reference
    output_key: str                  # Key to store output under
    parallel_group: str | None = None  # Steps with same group run concurrently
    condition: str | None = None     # Python expression for conditional execution
```

---

## Class: `StepResult`

Result from executing a single workflow step.

```python
@dataclass
class StepResult:
    step_name: str
    agent_name: str
    output: AgentOutput
    skipped: bool = False
    error: str | None = None
```

---

## Class: `Workflow`

A multi-agent workflow definition.

```python
@dataclass
class Workflow:
    name: str
    description: str
    steps: list[WorkflowStep]
    source_file: str = ""
```

### `workflow.slug`

URL-friendly identifier derived from the source filename.

- Type: `str` (property)

---

## Class: `WorkflowResult`

Complete result from a workflow execution.

```python
@dataclass
class WorkflowResult:
    workflow_name: str
    step_results: list[StepResult]
    total_latency_ms: float = 0.0
```

### `result.final_output`

The content from the last executed (non-skipped) step.

- Type: `str` (property)

### `result.all_outputs`

Map of `step_name → content` for all executed steps.

- Type: `dict[str, str]` (property)

### `result.total_tokens`

Aggregate token usage across all steps.

- Type: `dict[str, int]` (property) — Keys: `"input"`, `"output"`, `"total"`.

---

## Class: `WorkflowEngine`

Executes multi-agent workflows.

### Constructor

```python
WorkflowEngine(
    registry: AgentRegistry,
    runner: AgentRunner | None = None,
    config: Config | None = None,
    on_step_start: Callable | None = None,
    on_step_complete: Callable | None = None,
)
```

- `registry`: [`AgentRegistry`](registry.md) — For resolving agent references.
- `runner`: Optional [`AgentRunner`](runner.md). Created from config if `None`.
- `config`: Optional [`Config`](config.md).
- `on_step_start`: Callback `(step_name: str, agent_name: str) -> None`.
- `on_step_complete`: Callback `(step_name: str, result: StepResult) -> None`.

### `engine.run(workflow, workflow_input)`

Execute a workflow synchronously.

- `workflow`: `Workflow`
- `workflow_input`: `dict[str, Any]` — Input data for the workflow.
- Returns: `WorkflowResult`

```python
from runtime.workflow import WorkflowEngine, load_workflow
from runtime.registry import AgentRegistry
from pathlib import Path

registry = AgentRegistry.from_directory(Path("content-design"))
engine = WorkflowEngine(registry=registry)

workflow = load_workflow(Path("workflows/content-audit.yaml"))
result = engine.run(workflow, {
    "content": "Welcome! Click here to get started.",
    "brand_guidelines": "Friendly and professional",
    "target_audience": "New users",
})

print(result.final_output)
print(f"Total tokens: {result.total_tokens}")
```

### Execution Model

Steps run sequentially by default. Steps sharing the same `parallel_group`
value run concurrently using threads.

```yaml
steps:
  - name: step_a
    agent: generalist
    # Runs first (sequential)

  - name: step_b
    agent: tone
    parallel_group: "quality"
    # Runs concurrently with step_c

  - name: step_c
    agent: a11y
    parallel_group: "quality"
    # Runs concurrently with step_b

  - name: step_d
    agent: microcopy
    # Runs last (sequential, after parallel group)
```

### Input Reference Resolution

The `input_map` supports three reference patterns:

| Pattern | Resolves To |
| --- | --- |
| `$input.<field>` | Workflow input field |
| `$steps.<step_name>.content` | Previous step's output content |
| `$steps.<step_name>.<field>` | Previous step's output field |
| (literal string) | Used as-is |

### Conditional Execution

Steps can include a `condition` that is evaluated safely using AST parsing.
Only comparisons, boolean logic, attribute access, and literals are allowed — no
function calls or arbitrary code.

```yaml
- name: mobile_check
  agent: mobile
  condition: "input.platform == 'mobile'"
  input_map:
    content: "$input.content"
```

**Allowed operations:** `==`, `!=`, `<`, `>`, `<=`, `>=`, `in`, `not in`,
`and`, `or`, `not`, `+`, `-`, `*`, ternary `if/else`.

---

## `load_workflow(filepath)`

Load a workflow definition from a YAML file.

- `filepath`: `pathlib.Path`
- Returns: `Workflow`

## `load_workflows_from_directory(directory)`

Load all workflow YAML files from a directory (excludes `schema.yaml`).

- `directory`: `pathlib.Path`
- Returns: `list[Workflow]`

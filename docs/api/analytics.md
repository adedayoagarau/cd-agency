# `tools.analytics` — Usage Analytics

> Stability: Stable

```python
from tools.analytics import Analytics, AgentUsage
```

Local usage tracking and reporting. All data stored locally in
`.cd-agency/analytics.json` — nothing is sent externally.

## Class: `AgentUsage`

Tracks usage of a single agent.

```python
@dataclass
class AgentUsage:
    agent_name: str
    run_count: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency_ms: float = 0.0
    last_used: float = 0.0
    scores: list[float] = field(default_factory=list)
```

### `usage.avg_latency_ms`

Average latency across all runs.

- Type: `float` (property)

### `usage.avg_score`

Average quality score across scored runs.

- Type: `float` (property)

---

## Class: `Analytics`

Local analytics store.

```python
@dataclass
class Analytics:
    agents: dict[str, AgentUsage]
    workflow_runs: dict[str, int]
    content_types: dict[str, int]
    total_runs: int = 0
    first_run: float = 0.0
```

### `Analytics.load(project_dir)`

Load analytics from disk.

- `project_dir`: `Path | None` — Defaults to current directory.
- Returns: `Analytics`

### `analytics.save()`

Persist to disk. Called automatically by `record_agent_run()` and
`record_workflow_run()`.

### `analytics.record_agent_run(...)`

Record an agent execution.

- `agent_name`: `str`
- `input_tokens`: `int`
- `output_tokens`: `int`
- `latency_ms`: `float`
- `score`: `float | None` — Quality score (optional).
- `content_type`: `str` — Default `"general"`.

### `analytics.record_workflow_run(workflow_name)`

Record a workflow execution.

- `workflow_name`: `str`

### `analytics.top_agents(n)`

Get most-used agents.

- `n`: `int` — Number of agents to return (default: 5).
- Returns: `list[AgentUsage]`

### `analytics.summary()`

Generate a summary report.

- Returns: `dict`

```python
summary = analytics.summary()
print(f"Total runs: {summary['total_runs']}")
print(f"Agents used: {summary['unique_agents_used']}")
print(f"Tokens: {summary['total_tokens']:,}")
```

### `analytics.export_csv()`

Export analytics as CSV string.

- Returns: `str`

Columns: `Agent`, `Runs`, `Avg Latency (ms)`, `Avg Score`, `Total Tokens`.

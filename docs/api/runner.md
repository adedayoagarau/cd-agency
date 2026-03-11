# `runtime.runner` — Agent Runner

> Stability: Stable

```python
from runtime.runner import AgentRunner, run_agent
```

Executes content design agents via the Anthropic Claude API.

## Class: `AgentRunner`

### Constructor

```python
AgentRunner(config: Config | None = None)
```

- `config`: Optional [`Config`](config.md) instance. If `None`, loads from
  environment.

The Anthropic client is lazy-initialized on first use.

---

### `runner.run(agent, user_input, *, model, max_tokens, temperature, stream)`

Execute an agent with the given input.

- `agent`: [`Agent`](agent.md) — The agent to execute.
- `user_input`: `dict[str, Any]` — Input fields matching the agent's schema.
- `model`: `str | None` — Override the default model.
- `max_tokens`: `int | None` — Override the default max tokens.
- `temperature`: `float | None` — Override the default temperature.
- `stream`: `bool` — If `True`, use streaming API (default: `False`).
- Returns: [`AgentOutput`](agent.md#class-agentoutput)
- Raises:
  - `ValueError` if required inputs are missing.
  - `anthropic.APIError` if the API call fails after retries.

```python
from runtime.runner import AgentRunner
from runtime.registry import AgentRegistry
from pathlib import Path

registry = AgentRegistry.from_directory(Path("content-design"))
agent = registry.get("error")

runner = AgentRunner()
result = runner.run(agent, {
    "error_scenario": "Invalid email format",
    "severity": "warning",
})

print(result.content)
print(f"Tokens: {result.input_tokens} → {result.output_tokens}")
print(f"Latency: {result.latency_ms:.0f}ms")
```

### System Message Composition

The system message sent to the API is composed from:

1. Agent's built system message (`agent.build_system_message()`)
2. Product context block (if configured)
3. Project memory context (if entries exist)

Each section is separated by `---`.

### Retry Behavior

| Error Type | Retry? | Notes |
| --- | --- | --- |
| 4xx (except 429) | No | Client errors are not retried |
| 429 (Rate Limit) | Yes | Exponential backoff: 1s, 2s, 4s... |
| 5xx | Yes | Server errors with exponential backoff |
| Connection Error | Yes | Network issues with exponential backoff |

Maximum retries are controlled by `config.max_retries` (default: 3).

---

## `run_agent(agent, user_input, config, **kwargs)`

Convenience function to run an agent without creating a runner.

- `agent`: [`Agent`](agent.md)
- `user_input`: `dict[str, Any]`
- `config`: `Config | None`
- `**kwargs`: Passed to `AgentRunner.run()`
- Returns: [`AgentOutput`](agent.md#class-agentoutput)

```python
from runtime.runner import run_agent

result = run_agent(agent, {"error_scenario": "timeout"})
```

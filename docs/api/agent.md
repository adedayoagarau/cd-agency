# `runtime.agent` — Agent Model

> Stability: Stable

```python
from runtime.agent import Agent, AgentInput, AgentOutput, OutputField
```

The `runtime.agent` module defines the core data types for content design
agents.

## Class: `AgentInput`

Defines an expected input field for an agent.

```python
@dataclass
class AgentInput:
    name: str
    type: str
    required: bool = True
    description: str = ""
```

### Properties

| Property | Type | Description |
| --- | --- | --- |
| `name` | `str` | Input field name (e.g., `"error_scenario"`) |
| `type` | `str` | Expected type (e.g., `"string"`, `"string[]"`) |
| `required` | `bool` | Whether the input is mandatory |
| `description` | `str` | Human-readable description |

---

## Class: `OutputField`

Defines an expected output field for an agent.

```python
@dataclass
class OutputField:
    name: str
    type: str
    description: str = ""
```

---

## Class: `AgentOutput`

Structured output from an agent execution.

```python
@dataclass
class AgentOutput:
    content: str
    agent_name: str
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    raw_response: Any = None
```

### Properties

| Property | Type | Description |
| --- | --- | --- |
| `content` | `str` | The agent's text response |
| `agent_name` | `str` | Name of the agent that produced this output |
| `model` | `str` | Model used (e.g., `"claude-sonnet-4-20250514"`) |
| `input_tokens` | `int` | Token count for the input |
| `output_tokens` | `int` | Token count for the output |
| `latency_ms` | `float` | Execution time in milliseconds |
| `raw_response` | `Any` | Raw Anthropic API response object |

---

## Class: `Agent`

A content design agent loaded from a markdown definition file.

```python
@dataclass
class Agent:
    name: str
    description: str
    color: str = ""
    version: str = "1.0.0"
    difficulty_level: str = "intermediate"
    tags: list[str] = field(default_factory=list)
    inputs: list[AgentInput] = field(default_factory=list)
    outputs: list[OutputField] = field(default_factory=list)
    related_agents: list[str] = field(default_factory=list)

    # Prompt components
    system_prompt: str = ""
    few_shot_examples: str = ""
    core_mission: str = ""
    critical_rules: str = ""
    technical_deliverables: str = ""
    workflow_process: str = ""
    success_metrics: str = ""

    # Source
    source_file: str = ""
```

### `agent.slug`

URL-friendly identifier derived from the source filename.

- Type: `str` (property)

```python
agent = Agent(name="Error Architect", source_file="content-design/error-message-architect.md")
print(agent.slug)  # "error-message-architect"
```

If no `source_file` is set, the slug is derived from the name by lowercasing
and replacing spaces with hyphens.

---

### `agent.build_system_message()`

Compose the full system message from agent prompt components.

- Returns: `str`

Concatenates `system_prompt`, `few_shot_examples`, and `critical_rules` with
`---` separators.

```python
system_msg = agent.build_system_message()
```

---

### `agent.build_user_message(user_input)`

Compose the user message from structured input fields.

- `user_input`: `dict[str, Any]` — Input fields as key-value pairs.
- Returns: `str`

Each non-empty field is formatted as `**Label:** value` (with underscores
replaced by spaces and title-cased).

```python
msg = agent.build_user_message({
    "error_scenario": "Invalid email format",
    "severity": "warning",
})
# "**Error Scenario:** Invalid email format\n**Severity:** warning"
```

---

### `agent.validate_input(user_input)`

Validate user input against the agent's defined input schema.

- `user_input`: `dict[str, Any]`
- Returns: `list[str]` — List of error messages. Empty list means valid.

```python
errors = agent.validate_input({"error_scenario": "timeout"})
if errors:
    raise ValueError("; ".join(errors))
```

Checks:

1. Required fields must be present in the dict.
2. Required fields must not be empty/falsy.
3. Optional fields are not validated.

---

### `agent.get_required_inputs()`

Return only the required inputs.

- Returns: `list[AgentInput]`

---

### `agent.get_optional_inputs()`

Return only the optional inputs.

- Returns: `list[AgentInput]`

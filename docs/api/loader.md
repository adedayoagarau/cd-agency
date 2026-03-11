# `runtime.loader` — Agent Loader

> Stability: Stable

```python
from runtime.loader import load_agent, load_agents_from_directory
```

Parses Markdown agent definition files into `Agent` objects.

## `load_agent(filepath)`

Load a single agent from a Markdown file.

- `filepath`: `pathlib.Path` — Path to the `.md` agent file.
- Returns: [`Agent`](agent.md)
- Raises: `Exception` if the file cannot be parsed.

```python
from pathlib import Path
from runtime.loader import load_agent

agent = load_agent(Path("content-design/error-message-architect.md"))
print(agent.name)        # "Error Message Architect"
print(agent.slug)        # "error-message-architect"
print(len(agent.inputs)) # 5
```

### Parsing Process

1. **YAML Frontmatter** — Extracted from `---` delimited block at the top of
   the file. Parsed with `yaml.safe_load`.
2. **Markdown Sections** — The body is split by `###` headers into named
   sections (case-insensitive). Each section becomes an agent field.

### Frontmatter Fields

| Field | Type | Maps To |
| --- | --- | --- |
| `name` | string | `Agent.name` |
| `description` | string | `Agent.description` |
| `color` | string | `Agent.color` |
| `version` | string | `Agent.version` |
| `difficulty_level` | string | `Agent.difficulty_level` |
| `tags` | list | `Agent.tags` |
| `inputs` | list of objects | `Agent.inputs` (as `AgentInput`) |
| `outputs` | list of objects | `Agent.outputs` (as `OutputField`) |
| `related_agents` | list | `Agent.related_agents` |

### Markdown Sections (by `###` header)

| Section Header | Maps To |
| --- | --- |
| `### System Prompt` | `Agent.system_prompt` |
| `### Few-Shot Examples` | `Agent.few_shot_examples` |
| `### Core Mission` | `Agent.core_mission` |
| `### Critical Rules` | `Agent.critical_rules` |
| `### Technical Deliverables` | `Agent.technical_deliverables` |
| `### Workflow Process` | `Agent.workflow_process` |
| `### Success Metrics` | `Agent.success_metrics` |

---

## `load_agents_from_directory(directory)`

Load all agent files from a directory.

- `directory`: `pathlib.Path` — Directory containing `.md` files.
- Returns: `list[Agent]` — Sorted by filename.

If the directory does not exist, returns an empty list. Individual parse errors
are logged as warnings but do not halt loading.

```python
from pathlib import Path
from runtime.loader import load_agents_from_directory

agents = load_agents_from_directory(Path("content-design"))
print(f"Loaded {len(agents)} agents")  # "Loaded 15 agents"
```

---

## Internal Functions

### `_parse_frontmatter(text)`

Extract YAML frontmatter and remaining body from markdown text.

- `text`: `str`
- Returns: `tuple[dict, str]` — (frontmatter dict, body string)

If no frontmatter is found, returns `({}, text)`.

### `_parse_sections(body)`

Parse markdown body into named sections by `###` headers.

- `body`: `str`
- Returns: `dict[str, str]` — Section name (lowercased) → content

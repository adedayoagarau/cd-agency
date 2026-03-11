# `runtime.memory` — Project Memory

> Stability: Stable

```python
from runtime.memory import ProjectMemory, MemoryEntry
```

Project-level memory store for cross-session agent context. Agents can read from
memory (e.g., "Last time we decided to use 'workspace' not 'project'") and
decisions persist between CLI sessions.

Memory is stored in `.cd-agency/memory.json` in the project directory.

## Class: `MemoryEntry`

A single memory entry.

```python
@dataclass
class MemoryEntry:
    key: str
    value: str
    category: str          # terminology, voice, pattern, decision
    source_agent: str = ""
    timestamp: float = 0.0  # auto-set to time.time()
    metadata: dict[str, Any] = field(default_factory=dict)
```

---

## Class: `ProjectMemory`

Project-scoped memory store backed by a JSON file.

### `ProjectMemory.load(project_dir)`

Load memory from the project directory.

- `project_dir`: `Path | None` — Defaults to current directory.
- Returns: `ProjectMemory`

```python
memory = ProjectMemory.load()
print(len(memory))  # Number of entries
```

### `memory.save()`

Persist memory to disk. Called automatically by `remember()`, `forget()`, and
`clear()`.

### `memory.remember(key, value, category, source_agent, metadata)`

Store a memory entry.

- `key`: `str`
- `value`: `str`
- `category`: `str` — One of `"terminology"`, `"voice"`, `"pattern"`, `"decision"` (default: `"decision"`).
- `source_agent`: `str` — Agent that created this memory.
- `metadata`: `dict[str, Any] | None`

```python
memory.remember(
    "cta-style",
    "Always start CTAs with action verbs",
    category="pattern",
    source_agent="cta-optimization-specialist",
)
```

### `memory.recall(key)`

Retrieve a specific memory by key.

- `key`: `str`
- Returns: `MemoryEntry | None`

```python
entry = memory.recall("cta-style")
if entry:
    print(f"{entry.key}: {entry.value}")
```

### `memory.recall_by_category(category)`

Get all memories in a category.

- `category`: `str`
- Returns: `list[MemoryEntry]`

```python
terms = memory.recall_by_category("terminology")
for t in terms:
    print(f"  {t.key}: {t.value}")
```

### `memory.search(query)`

Search memories by key or value substring.

- `query`: `str` (case-insensitive)
- Returns: `list[MemoryEntry]`

### `memory.forget(key)`

Remove a memory entry.

- `key`: `str`
- Returns: `bool` — `True` if found and removed.

### `memory.clear()`

Clear all memory entries.

- Returns: `int` — Number of entries removed.

### `memory.get_context_for_agent(agent_name)`

Build a context string from memory for injection into agent prompts.

- `agent_name`: `str` (currently unused, reserved for agent-scoped memory)
- Returns: `str` — Formatted memory context, or `""` if empty.

Output is grouped by category:

```
## Project Memory

### Terminology Decisions
- **workspace-term**: Use 'workspace' not 'project'

### Voice & Tone Decisions
- tone-preference: Keep it friendly

### Content Patterns
- cta-style: Start with action verbs

### Past Decisions
- date-format: Use ISO 8601 dates
```

### `memory.to_dict()`

Export memory as a dictionary.

- Returns: `dict` with keys: `project`, `entry_count`, `categories`, `entries`.

### Storage Format

```json
{
  "version": "1.0",
  "entries": {
    "workspace-term": {
      "key": "workspace-term",
      "value": "Use 'workspace' not 'project'",
      "category": "terminology",
      "source_agent": "content-designer-generalist",
      "timestamp": 1710000000.0,
      "metadata": {}
    }
  }
}
```

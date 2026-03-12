# `runtime.versioning` — Content Versioning

> Stability: Experimental

```python
from runtime.versioning import ContentVersion, ContentHistory
```

Tracks before/after for every agent run. Every time an agent transforms content,
a version is automatically recorded so you can browse, search, diff, and audit
content changes over time.

## How It Works

The runner automatically calls `ContentHistory.record()` after each agent run.
Versions are stored in `.cd-agency/content_versions.json` in your project
directory, capped at 200 entries.

## Class: `ContentVersion`

A single version entry tracking an agent transformation.

```python
@dataclass
class ContentVersion:
    id: str                              # Short hash ID
    timestamp: float                     # Unix timestamp
    agent_name: str                      # Full agent name
    agent_slug: str                      # Agent slug
    input_text: str                      # Before text
    output_text: str                     # After text
    input_fields: dict[str, str] = {}    # All input fields
    model: str = ""                      # Model used
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    tags: list[str] = []
    notes: str = ""
```

### Properties

- `input_preview` — First 80 characters of input text
- `output_preview` — First 80 characters of output text

## Class: `ContentHistory`

Versioned content history backed by a JSON file.

### `ContentHistory.load(project_dir=None)`

Load version history from disk.

- `project_dir`: `Path | None` — Project root (defaults to current directory)
- Returns: `ContentHistory`

### `history.record(agent_name, agent_slug, input_text, output_text, ...)`

Record a new content version.

- Returns: `ContentVersion` — The newly created version

### `history.get(version_id)`

Get a specific version by ID.

- Returns: `ContentVersion | None`

### `history.list_recent(count=20)`

Get the most recent versions.

- Returns: `list[ContentVersion]`

### `history.list_by_agent(agent_slug)`

Get all versions for a specific agent.

- Returns: `list[ContentVersion]`

### `history.search(query)`

Search versions by input or output text.

- Returns: `list[ContentVersion]`

### `history.diff(version_id)`

Get a compact before/after diff for a version.

- Returns: `dict | None` with keys: `id`, `agent`, `before`, `after`,
  `before_len`, `after_len`, `char_delta`

### `history.summary()`

Get aggregate statistics.

- Returns: `dict` with keys: `count`, `agents_used`, `latest`

### `history.clear()`

Delete all versions.

- Returns: `int` — Number of versions cleared

## CLI Usage

```bash
cd-agency history list                  # Recent versions
cd-agency history list -a error -n 5    # Filter by agent
cd-agency history show abc123           # Full before/after
cd-agency history diff abc123           # Compact diff
cd-agency history search "payment"      # Search by text
cd-agency history stats                 # Aggregate stats
cd-agency history clear                 # Delete all
```

## MCP Usage

The `content_history` MCP tool exposes the same functionality to AI clients:

```
"Give me the last 5 content versions"
"Diff version abc123"
"Search history for payment-related content"
```

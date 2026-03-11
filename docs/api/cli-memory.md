# `memory` Commands

> Stability: Stable

Manage project-level memory — terminology decisions, voice preferences, content
patterns, and past decisions that persist across sessions.

Memory is stored locally in `.cd-agency/memory.json` and is automatically
injected into agent prompts when running agents.

```bash
cd-agency memory COMMAND [ARGS]
```

## `memory show`

Display stored project memory.

```bash
cd-agency memory show [OPTIONS]
```

**Options:**

| Option | Short | Type | Description |
| --- | --- | --- | --- |
| `--category` | `-c` | string | Filter by category |
| `--json-output` | | flag | Output as JSON |

**Categories:**

| Category | Purpose |
| --- | --- |
| `terminology` | Word choices (e.g., "Use 'workspace' not 'project'") |
| `voice` | Tone and voice decisions |
| `pattern` | Content patterns and templates |
| `decision` | General design decisions |

**Example:**

```bash
cd-agency memory show -c terminology
```

---

## `memory add`

Store a memory entry.

```bash
cd-agency memory add KEY VALUE [OPTIONS]
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `KEY` | Memory key (e.g., `"workspace-term"`) |
| `VALUE` | Memory value (e.g., `"Use 'workspace' not 'project'"`) |

**Options:**

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--category` | `-c` | choice | `decision` | Category (see above) |
| `--agent` | | string | `""` | Source agent name |

**Example:**

```bash
cd-agency memory add "workspace-term" \
  "Always use 'workspace' instead of 'project'" \
  -c terminology

cd-agency memory add "tone-preference" \
  "Keep error messages empathetic, never blame the user" \
  -c voice --agent "tone-evaluation-agent"
```

---

## `memory clear`

Clear all project memory (with confirmation prompt).

```bash
cd-agency memory clear
```

---

## `memory export`

Export memory as JSON or CSV.

```bash
cd-agency memory export [OPTIONS]
```

**Options:**

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--format` | `-f` | choice | `json` | Export format: `json` or `csv` |

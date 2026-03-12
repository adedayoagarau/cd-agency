# `history` Commands

> Stability: Experimental

Browse content version history. Every agent run automatically records a
before/after snapshot, so you can track how your content evolved over time.

```bash
cd-agency history COMMAND [ARGS]
```

## `history list`

List recent content versions.

```bash
cd-agency history list [OPTIONS]
```

**Options:**

| Option | Short | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `--agent` | `-a` | string | | Filter by agent slug |
| `--count` | `-n` | int | `20` | Number of recent versions to show |
| `--json-output` | | flag | | Output as JSON |

**Examples:**

```bash
# Show last 20 versions
cd-agency history list

# Show last 5 versions from the error agent
cd-agency history list --agent error-message-architect -n 5

# JSON output
cd-agency history list --json-output
```

---

## `history show`

Show a specific content version with full before/after text.

```bash
cd-agency history show VERSION_ID [OPTIONS]
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `VERSION_ID` | The version ID (shown in `history list` output) |

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |

**Example:**

```bash
cd-agency history show abc123
```

```
Version abc123 — 2026-03-12 14:30:22
Agent: Error Message Architect | Model: claude-sonnet-4-20250514
Tokens: 1234→567 | 2340ms

Input Fields:
  error_scenario: File upload exceeds 10MB limit
  severity: warning

Before (Input):
  File upload exceeds 10MB limit

After (Output):
  Your file is too large to upload. Try a file under 10 MB, or compress it first.
```

---

## `history diff`

Show a compact before/after diff for a version.

```bash
cd-agency history diff VERSION_ID [OPTIONS]
```

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |

**Example:**

```bash
cd-agency history diff abc123
```

```
Diff: abc123 (error-message-architect)
- File upload exceeds 10MB limit
+ Your file is too large to upload. Try a file under 10 MB, or compress it first.

35 → 76 chars (longer: +41)
```

---

## `history search`

Search content history by input or output text.

```bash
cd-agency history search QUERY [OPTIONS]
```

**Arguments:**

| Argument | Description |
| --- | --- |
| `QUERY` | Text to search for in input or output fields |

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |

**Example:**

```bash
cd-agency history search "payment"
```

---

## `history stats`

Show content versioning statistics.

```bash
cd-agency history stats [OPTIONS]
```

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |

**Example:**

```bash
cd-agency history stats
```

```
Content Version Stats
  Total versions: 42
  Agents used: error-message-architect, cta-optimization-specialist, mobile-ux-writer
  Latest: error-message-architect — File upload exceeds 10MB limit
```

---

## `history clear`

Clear all content version history. Prompts for confirmation.

```bash
cd-agency history clear
```

---

## Storage

Content versions are stored in `.cd-agency/content_versions.json` in your
project directory. The history is capped at 200 versions — oldest entries are
automatically pruned when the cap is reached.

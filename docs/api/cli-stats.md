# `stats` Command

> Stability: Stable

Display local usage analytics. All data is stored locally in
`.cd-agency/analytics.json` — nothing is sent externally.

```bash
cd-agency stats [OPTIONS]
```

## Options

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |
| `--csv-output` | flag | Output as CSV |

## Dashboard Output

```bash
cd-agency stats
```

```
CD Agency Usage Stats
Total runs: 47
Unique agents: 8
Total tokens: 156,234

                Top Agents
┏━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┓
┃ Agent                   ┃ Runs ┃ Avg Score ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━┩
│ Error Message Architect │   12 │      8.2  │
│ Microcopy Review Agent  │    9 │      7.5  │
│ CTA Optimization        │    8 │        -  │
└─────────────────────────┴──────┴───────────┘
```

## Tracked Metrics

| Metric | Description |
| --- | --- |
| `total_runs` | Total agent executions |
| `unique_agents_used` | Number of distinct agents used |
| `unique_workflows_used` | Number of distinct workflows used |
| `top_agents` | Most-used agents with run counts and avg scores |
| `content_types` | Breakdown by content type |
| `total_tokens` | Aggregate token usage |

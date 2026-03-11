# `runtime.registry` — Agent Registry

> Stability: Stable

```python
from runtime.registry import AgentRegistry
```

Central lookup for all available agents. Supports lookup by name, slug, alias,
or tag.

## Class: `AgentRegistry`

### Constructor

```python
AgentRegistry(agents: list[Agent] | None = None)
```

- `agents`: Optional list of agents to register immediately.

### `AgentRegistry.from_directory(directory)`

Class method. Load all agents from a directory and build the registry.

- `directory`: `pathlib.Path`
- Returns: `AgentRegistry`

```python
from pathlib import Path
registry = AgentRegistry.from_directory(Path("content-design"))
print(registry.count)  # 15
```

---

### `registry.register(agent)`

Register an agent in the registry.

- `agent`: [`Agent`](agent.md)

```python
registry.register(my_custom_agent)
```

---

### `registry.get(name)`

Look up an agent by name, slug, or alias.

- `name`: `str` — Agent slug, alias, or full name (case-insensitive).
- Returns: `Agent | None`

Lookup order:

1. Direct slug match
2. Alias match (see [aliases](#default-aliases))
3. Fuzzy match on `agent.name` (lowercased)

```python
# All of these return the same agent:
registry.get("error-message-architect")  # by slug
registry.get("error")                     # by alias
registry.get("Error Message Architect")   # by name
```

---

### `registry.list_all()`

Return all registered agents sorted by name.

- Returns: `list[Agent]`

---

### `registry.filter_by_tag(tag)`

Return agents that have a specific tag.

- `tag`: `str` (case-insensitive)
- Returns: `list[Agent]`

```python
error_agents = registry.filter_by_tag("errors")
a11y_agents = registry.filter_by_tag("accessibility")
```

---

### `registry.filter_by_difficulty(level)`

Return agents at a specific difficulty level.

- `level`: `str` — One of `"beginner"`, `"intermediate"`, `"advanced"`.
- Returns: `list[Agent]`

---

### `registry.search(query)`

Search agents by name, description, or tags.

- `query`: `str` (case-insensitive substring match)
- Returns: `list[Agent]` — Sorted by name.

```python
results = registry.search("mobile")
# Returns: [Mobile UX Writer]
```

---

### `registry.add_alias(alias, slug)`

Add a custom alias for an agent slug.

- `alias`: `str`
- `slug`: `str` — Must match a registered agent's slug.

```python
registry.add_alias("err", "error-message-architect")
agent = registry.get("err")  # Works!
```

---

### `registry.count`

Number of registered agents.

- Type: `int` (property)

---

### `registry.__contains__(name)`

Check if an agent exists in the registry.

```python
if "error" in registry:
    print("Error agent is available")
```

---

## Default Aliases

| Alias | Agent Slug |
| --- | --- |
| `generalist`, `general` | `content-designer-generalist` |
| `error`, `errors` | `error-message-architect` |
| `microcopy` | `microcopy-review-agent` |
| `tone`, `voice` | `tone-evaluation-agent` |
| `a11y`, `accessibility`, `wcag` | `accessibility-content-auditor` |
| `cta` | `cta-optimization-specialist` |
| `onboarding` | `onboarding-flow-designer` |
| `docs`, `tech-docs` | `technical-documentation-writer` |
| `mobile` | `mobile-ux-writer` |
| `l10n`, `localization`, `i18n` | `localization-content-strategist` |
| `notifications`, `notify`, `push` | `notification-content-designer` |
| `privacy`, `legal` | `privacy-legal-content-simplifier` |
| `empty`, `placeholder` | `empty-state-placeholder-specialist` |
| `search` | `search-experience-writer` |
| `chatbot`, `conversation` | `conversational-ai-designer` |

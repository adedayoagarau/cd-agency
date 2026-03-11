# `context` Commands

> Stability: Stable

Manage product context — domain, audience, tone, and content guidelines. Product
context is automatically injected into every agent's system prompt.

```bash
cd-agency context COMMAND [ARGS]
```

## `context show`

Display the current product context.

```bash
cd-agency context show [OPTIONS]
```

**Options:**

| Option | Type | Description |
| --- | --- | --- |
| `--json-output` | flag | Output as JSON |

---

## `context init`

Interactively set up product context for your project.

```bash
cd-agency context init
```

Prompts for:

- Product name
- Product description (1–2 sentences)
- Domain (e.g., fintech, healthcare, SaaS)
- Target audience
- Tone (e.g., professional but friendly)
- Platform (e.g., web app, mobile)
- Content guidelines (comma-separated)

Saves to `.cd-agency.yaml`.

---

## `context set`

Set a single product context field.

```bash
cd-agency context set KEY VALUE
```

**Arguments:**

| Argument | Type | Description |
| --- | --- | --- |
| `KEY` | choice | One of: `product_name`, `description`, `domain`, `audience`, `tone`, `platform` |
| `VALUE` | string | The value to set |

**Example:**

```bash
cd-agency context set product_name "Acme App"
cd-agency context set domain "fintech"
cd-agency context set audience "Small business owners"
cd-agency context set tone "Professional but approachable"
```

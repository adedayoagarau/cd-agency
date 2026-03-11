# `runtime.config` — Configuration

> Stability: Stable

```python
from runtime.config import Config, ProductContext
```

## Class: `ProductContext`

Product-level context injected into every agent prompt.

```python
@dataclass
class ProductContext:
    product_name: str = ""
    description: str = ""
    domain: str = ""
    audience: str = ""
    tone: str = ""
    platform: str = ""
    guidelines: list[str] = field(default_factory=list)
```

### `context.is_configured()`

Return `True` if any context field is set (checks `product_name`, `description`,
or `domain`).

- Returns: `bool`

### `context.build_context_block()`

Build a formatted context block for injection into agent system prompts.

- Returns: `str` — Markdown-formatted context block, or `""` if not configured.

```python
ctx = ProductContext(product_name="Acme", domain="fintech")
print(ctx.build_context_block())
```

```
## Product Context

**Product:** Acme
**Domain:** fintech

Use this product context to tailor all suggestions...
```

### `ProductContext.from_dict(data)`

Create from a dictionary (e.g., parsed from YAML config).

- `data`: `dict`
- Returns: `ProductContext`

### `context.to_dict()`

Export as a dictionary (only includes non-empty fields).

- Returns: `dict`

---

## Class: `Config`

Runtime configuration with config file and environment variable overrides.

```python
@dataclass
class Config:
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"
    agents_dir: Path = Path("content-design")
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: float = 60.0
    max_retries: int = 3
    default_preset: str = ""
    brand_voice_guide: str = ""
    output_format: str = "text"
    product_context: ProductContext = ProductContext()
```

### Priority Order

1. Environment variables (highest)
2. Config file (`.cd-agency.yaml`)
3. Defaults (lowest)

### `Config.from_env()`

Load configuration from config file + environment variables.

- Returns: `Config`

```python
config = Config.from_env()
print(config.model)     # "claude-sonnet-4-20250514"
print(config.api_key)   # From ANTHROPIC_API_KEY env var
```

### `config.validate()`

Return a list of configuration errors. Empty list means valid.

- Returns: `list[str]`

Checks:

1. `api_key` is not empty.
2. `agents_dir` exists as a directory.

```python
errors = config.validate()
if errors:
    for err in errors:
        print(f"Error: {err}")
```

### Config File Search

The following filenames are searched in order:

1. `.cd-agency.yaml`
2. `.cd-agency.yml`
3. `cd-agency.yaml`

### Environment Variables

| Variable | Config Field | Default |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | `api_key` | `""` |
| `CD_AGENCY_MODEL` | `model` | `"claude-sonnet-4-20250514"` |
| `CD_AGENCY_AGENTS_DIR` | `agents_dir` | `"content-design"` |
| `CD_AGENCY_MAX_TOKENS` | `max_tokens` | `4096` |
| `CD_AGENCY_TEMPERATURE` | `temperature` | `0.7` |
| `CD_AGENCY_TIMEOUT` | `timeout` | `60.0` |
| `CD_AGENCY_MAX_RETRIES` | `max_retries` | `3` |

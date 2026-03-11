# Configuration

> Stability: Stable

CD Agency uses a three-tier configuration system. Priority from highest to
lowest:

1. **Environment variables** (override everything)
2. **Config file** (`.cd-agency.yaml`)
3. **Defaults** (built into the code)

## Config File

CD Agency searches for config files in this order:

1. `.cd-agency.yaml`
2. `.cd-agency.yml`
3. `cd-agency.yaml`

All paths are relative to the current working directory.

### Full Example

```yaml
# .cd-agency.yaml
api_key: sk-ant-...           # Or use ANTHROPIC_API_KEY env var
model: claude-sonnet-4-20250514
agents_dir: content-design
max_tokens: 4096
temperature: 0.7
timeout: 60.0
max_retries: 3
default_preset: ""
brand_voice_guide: ""
output_format: text            # text | json | markdown

product_context:
  product_name: "Acme App"
  description: "Project management for small teams"
  domain: "SaaS"
  audience: "Small business owners"
  tone: "Professional but friendly"
  platform: "Web app"
  guidelines:
    - "No jargon"
    - "Use active voice"
    - "Keep buttons under 3 words"
```

## Environment Variables

| Variable | Default | Description |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | `""` | Anthropic API key for agent execution |
| `CD_AGENCY_MODEL` | `claude-sonnet-4-20250514` | Default Claude model |
| `CD_AGENCY_AGENTS_DIR` | `content-design` | Path to agent definition files |
| `CD_AGENCY_MAX_TOKENS` | `4096` | Maximum response tokens |
| `CD_AGENCY_TEMPERATURE` | `0.7` | Model temperature (0.0–1.0) |
| `CD_AGENCY_TIMEOUT` | `60.0` | API request timeout in seconds |
| `CD_AGENCY_MAX_RETRIES` | `3` | Number of retry attempts for API errors |

## Config Class

See [`runtime.config`](config.md) for the full Python API.

```python
from runtime.config import Config

# Load from env + config file
config = Config.from_env()

# Validate configuration
errors = config.validate()
if errors:
    print("Config errors:", errors)
```

## Product Context

Product context is injected into every agent's system prompt to tailor
suggestions to your specific product.

### Set Up Interactively

```bash
cd-agency context init
```

### Set Individual Fields

```bash
cd-agency context set product_name "Acme App"
cd-agency context set domain "fintech"
cd-agency context set audience "Small business owners"
```

### View Current Context

```bash
cd-agency context show
cd-agency context show --json-output
```

### Available Fields

| Field | Description | Example |
| --- | --- | --- |
| `product_name` | Your product's name | `"Acme App"` |
| `description` | What the product does | `"Project management for teams"` |
| `domain` | Industry or domain | `"fintech"`, `"healthcare"`, `"SaaS"` |
| `audience` | Target users | `"Small business owners"` |
| `tone` | Voice and tone | `"Professional but friendly"` |
| `platform` | Platform type | `"Web app"`, `"Mobile"`, `"Multi-platform"` |
| `guidelines` | Content rules (list) | `["No jargon", "Use active voice"]` |

## Security

- Config files (`.cd-agency.yaml`, `.cd-agency.yml`) are listed in `.gitignore`
  by default.
- API keys should be set via environment variables in production.
- Never commit API keys to version control.

# Integrations

CD Agency integrates with your existing design and development workflow through multiple channels.

## Paper.design (MCP)

CD Agency includes a [Model Context Protocol](https://modelcontextprotocol.io) server that lets AI agents in Paper.design read and interact with all content design agents, scoring tools, and presets directly.

### Setup

**Claude Code:**
```bash
claude mcp add cd-agency -- python -m mcp
```

**Cursor:** Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "cd-agency": {
      "command": "python",
      "args": ["-m", "mcp"],
      "cwd": "/path/to/cd-agency"
    }
  }
}
```

**VS Code Copilot:** Add to `.vscode/mcp.json`:
```json
{
  "servers": {
    "cd-agency": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "mcp"],
      "cwd": "/path/to/cd-agency"
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `list_agents` | List all content design agents |
| `get_agent_info` | Get details about a specific agent |
| `suggest_agent` | Auto-suggest the best agent for given text |
| `score_readability` | Flesch-Kincaid readability scoring |
| `lint_content` | UX writing best practices linter |
| `check_accessibility` | WCAG text accessibility checker |
| `score_all` | Run all scorers combined |
| `compare_text` | Before/after readability comparison |
| `validate_content` | Validate UI text against character limits, platform conventions, a11y, and localization expansion |
| `content_history` | Browse content version history — list, search, diff, stats |
| `list_presets` | List design system presets |
| `get_preset` | Get preset details |

### MCP Resources

- `cd-agency://agents` — Complete agent list as JSON
- `cd-agency://decision-tree` — Agent selection guide
- `cd-agency://presets` — Design system presets

---

## Figma Plugin

The Figma plugin lets designers run content design agents directly on text layers without leaving Figma.

### Setup

1. Start the API backend:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

2. Build the plugin:
```bash
cd figma-plugin && npm install && npm run build
```

3. In Figma: **Plugins > Development > Import plugin from manifest** → select `figma-plugin/manifest.json`

### Features

- Select text layer → auto-suggest agent → one-click apply
- Design system presets (Material, Polaris, Atlassian, Apple HIG)
- Inline scoring (readability, a11y, lint)
- Run history per file

---

## VS Code Extension

The VS Code extension provides inline content linting and agent access in your editor.

### Setup

1. Build the extension:
```bash
cd vscode-extension && npm install && npm run compile
```

2. Install: press `F5` in VS Code to launch the Extension Development Host

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| `CD Agency: Run Agent on Selection` | `Ctrl+Shift+A` | Run an agent on selected text |
| `CD Agency: Score Selected Text` | — | Score selection for readability |
| `CD Agency: List Available Agents` | — | Browse all agents |
| `CD Agency: Configure` | — | Set API URL and preferences |

### Auto-Lint

Enable `cdAgency.autoLint` in VS Code settings to automatically lint string literals in JS/TS/JSX/TSX files. Content issues appear as VS Code diagnostics (squiggly underlines).

---

## REST API

The FastAPI backend provides HTTP endpoints for any integration.

### Endpoints

All endpoints are under the `/api/v1` prefix. The agent run endpoint requires the agent slug in the URL path and accepts `{"input": {"text": "..."}, "preset": "material-design"}` as the request body.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/agents` | List all agents (returns slug, name, description, tags) |
| `GET` | `/api/v1/agents/{slug}` | Get full agent details including inputs/outputs |
| `POST` | `/api/v1/agents/{slug}/run` | Run an agent on input text |
| `GET` | `/api/v1/agents/search?q=` | Search agents by name/description/tags |
| `POST` | `/api/v1/score/readability` | Flesch-Kincaid readability scoring |
| `POST` | `/api/v1/score/lint` | Content linter (UX writing rules) |
| `POST` | `/api/v1/score/a11y` | WCAG accessibility text checker |
| `POST` | `/api/v1/score/all` | All scores combined (readability + lint + a11y) |
| `POST` | `/api/v1/validate` | Validate UI text against char limits, platform, a11y, localization |
| `GET` | `/api/v1/validate/element-types` | List all supported UI element types with default limits |
| `GET` | `/api/v1/history` | List recent content versions (`?agent=`, `?count=`) |
| `GET` | `/api/v1/history/stats` | Aggregate content versioning statistics |
| `GET` | `/api/v1/history/search?q=` | Search content history by input/output text |
| `GET` | `/api/v1/history/{id}` | Get a specific version with full before/after |
| `GET` | `/api/v1/history/{id}/diff` | Compact before/after diff for a version |
| `GET` | `/api/v1/presets` | List design system presets |
| `GET` | `/api/v1/presets/{name}` | Get preset voice guidelines |
| `GET` | `/health` | Health check |

Scoring endpoints accept `{"text": "your content here"}`. The validation endpoint accepts `{"text": "...", "element_type": "button", "platform": "ios", "target_language": "de"}`. Authentication is via `X-API-Key` header (optional, controlled by `CD_AGENCY_REQUIRE_AUTH` env var).

### Example: Validate Content

```bash
curl -X POST http://localhost:8000/api/v1/validate \
  -H "Content-Type: application/json" \
  -d '{"text": "Complete your purchase securely", "element_type": "button", "platform": "ios", "target_language": "de"}'
```

```json
{
  "passed": false,
  "error_count": 1,
  "warning_count": 2,
  "violations": [
    {"rule": "character_limit", "severity": "error", "message": "Button text exceeds 25 char limit (31 chars)"},
    {"rule": "localization_expansion", "severity": "warning", "message": "Text will expand to ~41 chars in DE (factor: 1.35x)..."},
    {"rule": "platform_case", "severity": "warning", "message": "IOS uses Title Case for buttons..."}
  ],
  "summary": "Constraint check: 1 error(s), 2 warning(s)"
}
```

### Example: Content History

```bash
# List recent versions
curl http://localhost:8000/api/v1/history?count=5

# Search history
curl http://localhost:8000/api/v1/history/search?q=payment

# Get diff
curl http://localhost:8000/api/v1/history/abc123/diff
```

### Run the API

```bash
pip install fastapi uvicorn
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -f api/Dockerfile -t cd-agency-api .
docker run -p 8000:8000 -e ANTHROPIC_API_KEY=your-key cd-agency-api
```

---

## GitHub Action

Use the content-lint GitHub Action to automatically check content quality in PRs.

```yaml
# .github/workflows/content-lint.yml
name: Content Lint
on: [pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: adedayoagarau/cd-agency/.github/actions/content-lint@main
        with:
          files: "**/*.json,**/*.md"
          severity: warning
```

The action scans changed files for UI strings and reports content quality issues as PR comments.

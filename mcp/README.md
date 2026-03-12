# CD Agency MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io) server that exposes CD Agency's content design agents, scoring tools, and linting as MCP tools — for use with [Paper.design](https://paper.design), Cursor, Claude Code, VS Code Copilot, and any MCP-compatible client.

## What It Does

The MCP server lets AI agents read and interact with CD Agency tools directly:

| Tool | Description |
|------|-------------|
| `list_agents` | List all content design agents |
| `get_agent_info` | Get details about a specific agent |
| `suggest_agent` | Auto-suggest the best agent for given text |
| `score_readability` | Flesch-Kincaid readability scoring |
| `lint_content` | UX writing best practices linter |
| `check_accessibility` | WCAG text accessibility checker |
| `score_all` | Run all scorers at once |
| `compare_text` | Before/after readability comparison |
| `validate_content` | Validate UI text against char limits, platform conventions, a11y, and localization expansion |
| `content_history` | Browse content version history — list, search, diff, stats |
| `list_presets` | List design system presets |
| `get_preset` | Get preset details (Material, Polaris, etc.) |

## Setup

### Paper.design

1. Make sure CD Agency is installed: `pip install cd-agency`
2. Start the MCP server in your terminal (Paper will connect via stdio)
3. In Paper, add the MCP server URL or connect via the Paper MCP settings

### Claude Code

```bash
claude mcp add cd-agency -- python -m mcp
```

### Cursor

Add to your `.cursor/mcp.json`:

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

### VS Code Copilot

Add to your `.vscode/mcp.json`:

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

## Resources

The server also exposes MCP resources:

- `cd-agency://agents` — Full agent list as JSON
- `cd-agency://decision-tree` — Agent selection guide
- `cd-agency://presets` — Design system presets

## Example Usage

Once connected, you can ask your AI assistant things like:

- "Score this button text for readability: 'Submit your application now'"
- "Which agent should I use to improve this error message?"
- "Lint this notification copy for accessibility issues"
- "Compare the readability of these two versions of my CTA"
- "Show me the Material Design voice guidelines"
- "Validate this toast text for iOS: 'Changes saved successfully'"
- "Show me my recent content version history"
- "Diff version abc123 — what changed?"

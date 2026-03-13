"""CD Agency MCP Server.

Exposes content design agents, scoring tools, and linting as MCP tools
for use with Paper.design, Cursor, Claude Code, VS Code Copilot, and
any other MCP-compatible client.

Run standalone:
    python -m mcp.server

Or add to Claude Code:
    claude mcp add cd-agency -- python -m mcp.server
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Ensure project root is on the path
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from runtime.agent import Agent
from runtime.loader import load_agents_from_directory
from runtime.registry import AgentRegistry
from tools.scoring import ReadabilityScorer
from tools.linter import ContentLinter
from tools.a11y_checker import A11yChecker

# ---------------------------------------------------------------------------
# MCP Protocol helpers (Streamable HTTP / stdio)
# ---------------------------------------------------------------------------

_CONTENT_DESIGN_DIR = Path(__file__).parent.parent / "content-design"
_PRESETS_DIR = Path(__file__).parent.parent / "presets"

# Lazy-loaded singletons
_registry: AgentRegistry | None = None
_scorer: ReadabilityScorer | None = None
_linter: ContentLinter | None = None
_a11y: A11yChecker | None = None


def _get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry.from_directory(_CONTENT_DESIGN_DIR)
    return _registry


def _get_scorer() -> ReadabilityScorer:
    global _scorer
    if _scorer is None:
        _scorer = ReadabilityScorer()
    return _scorer


def _get_linter() -> ContentLinter:
    global _linter
    if _linter is None:
        _linter = ContentLinter()
    return _linter


def _get_a11y() -> A11yChecker:
    global _a11y
    if _a11y is None:
        _a11y = A11yChecker()
    return _a11y


# ---------------------------------------------------------------------------
# Tool definitions (MCP tool schema)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "list_agents",
        "description": "List all content design agents available in CD Agency. Returns agent names, slugs, descriptions, and tags.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "Optional tag to filter agents (e.g., 'microcopy', 'error', 'accessibility')",
                },
            },
        },
    },
    {
        "name": "get_agent_info",
        "description": "Get detailed information about a specific content design agent, including its inputs, outputs, and related agents.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Agent name or slug (e.g., 'error', 'cta', 'microcopy', 'error-message-architect')",
                },
            },
            "required": ["agent"],
        },
    },
    {
        "name": "suggest_agent",
        "description": "Given a piece of UI text, suggest which content design agent would be most appropriate to improve it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The UI text to analyze",
                },
                "context": {
                    "type": "string",
                    "description": "Optional context (e.g., 'error message', 'CTA button', 'onboarding step', 'tooltip')",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "score_readability",
        "description": "Score text for readability using Flesch-Kincaid grade level and reading ease. Returns grade, ease score, word count, sentence analysis, and complexity index.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to score for readability",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "lint_content",
        "description": "Run the content linter on text to check for UX writing best practices: action verbs in CTAs, mobile character limits, jargon, inclusive language, passive voice, and more.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to lint",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "check_accessibility",
        "description": "Check text for accessibility compliance (WCAG). Flags ALL CAPS, complex sentences, emoji overuse, unclear link text, and high reading levels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to check for accessibility",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "score_all",
        "description": "Run all scoring tools (readability, lint, accessibility) on text and return a combined report.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to score",
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "compare_text",
        "description": "Compare two versions of text (before/after) and return readability improvement metrics.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "before": {
                    "type": "string",
                    "description": "The original text",
                },
                "after": {
                    "type": "string",
                    "description": "The improved text",
                },
            },
            "required": ["before", "after"],
        },
    },
    {
        "name": "validate_content",
        "description": "Validate UI text against character limits, platform conventions, accessibility, and localization expansion rules. Specify the element type (button, toast, tooltip, etc.) for accurate limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The UI text to validate",
                },
                "element_type": {
                    "type": "string",
                    "description": "UI element type (button, tooltip, toast, push_title, push_body, modal_headline, modal_body, inline_error, placeholder, badge, etc.)",
                },
                "platform": {
                    "type": "string",
                    "description": "Target platform: 'ios', 'android', or 'web' (optional)",
                },
                "target_language": {
                    "type": "string",
                    "description": "Target language code for localization expansion check, e.g. 'de', 'fr', 'ja' (optional)",
                },
            },
            "required": ["text", "element_type"],
        },
    },
    {
        "name": "content_history",
        "description": "Browse content version history — see before/after for past agent runs. Actions: 'list' (recent versions), 'search' (by text), 'diff' (before/after for a version ID), 'stats' (summary).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform: 'list', 'search', 'diff', 'stats'",
                    "enum": ["list", "search", "diff", "stats"],
                },
                "query": {
                    "type": "string",
                    "description": "Search query (for 'search' action) or version ID (for 'diff' action)",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of recent versions to return (for 'list' action, default 10)",
                },
            },
            "required": ["action"],
        },
    },
    {
        "name": "list_presets",
        "description": "List available design system presets (Material Design, Shopify Polaris, Atlassian, Apple HIG).",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_preset",
        "description": "Get details of a design system preset including voice guide, terminology, and character limits.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Preset name (e.g., 'material-design', 'shopify-polaris', 'atlassian-design', 'apple-hig')",
                },
            },
            "required": ["name"],
        },
    },
]

# ---------------------------------------------------------------------------
# Resource definitions
# ---------------------------------------------------------------------------

RESOURCES = [
    {
        "uri": "cd-agency://agents",
        "name": "Content Design Agents",
        "description": "Complete list of all content design agents with their capabilities",
        "mimeType": "application/json",
    },
    {
        "uri": "cd-agency://decision-tree",
        "name": "Agent Decision Tree",
        "description": "Guide for choosing the right agent based on your content task",
        "mimeType": "text/markdown",
    },
    {
        "uri": "cd-agency://presets",
        "name": "Design System Presets",
        "description": "Available design system voice profiles",
        "mimeType": "application/json",
    },
]

# ---------------------------------------------------------------------------
# Tool execution
# ---------------------------------------------------------------------------


def _agent_to_dict(agent: Agent) -> dict[str, Any]:
    return {
        "name": agent.name,
        "slug": agent.slug,
        "description": agent.description,
        "tags": agent.tags,
        "difficulty_level": agent.difficulty_level,
        "inputs": [{"name": i.name, "type": i.type, "required": i.required, "description": i.description} for i in agent.inputs],
        "outputs": [{"name": o.name, "type": o.type, "description": o.description} for o in agent.outputs],
        "related_agents": agent.related_agents,
    }


def _suggest_agent_for_text(text: str, context: str = "") -> dict[str, Any]:
    """Heuristic agent suggestion based on text content."""
    lower = (text + " " + context).lower()
    suggestions = []

    if any(w in lower for w in ["error", "fail", "wrong", "invalid", "couldn't", "unable"]):
        suggestions.append(("error-message-architect", "Text contains error-related language"))
    if any(w in lower for w in ["click", "start", "sign up", "subscribe", "buy", "try", "get"]):
        suggestions.append(("cta-optimization-specialist", "Text appears to be a call-to-action"))
    if any(w in lower for w in ["welcome", "get started", "step", "next", "onboard"]):
        suggestions.append(("onboarding-flow-designer", "Text appears to be onboarding content"))
    if any(w in lower for w in ["notification", "alert", "remind", "update", "push"]):
        suggestions.append(("notification-content-designer", "Text appears to be a notification"))
    if any(w in lower for w in ["search", "find", "no results", "looking for"]):
        suggestions.append(("search-experience-writer", "Text appears to be search-related"))
    if any(w in lower for w in ["empty", "nothing here", "no items", "get started"]):
        suggestions.append(("empty-state-placeholder-specialist", "Text appears to be an empty state"))
    if any(w in lower for w in ["privacy", "data", "consent", "cookie", "terms"]):
        suggestions.append(("privacy-legal-content-simplifier", "Text contains privacy/legal language"))
    if any(w in lower for w in ["accessible", "a11y", "screen reader", "alt text", "wcag"]):
        suggestions.append(("accessibility-content-auditor", "Text may need accessibility review"))
    if any(w in lower for w in ["tone", "voice", "brand", "mood", "feel"]):
        suggestions.append(("tone-evaluation-agent", "Text may benefit from tone evaluation"))
    if any(w in lower for w in ["mobile", "app", "phone", "tap", "swipe"]):
        suggestions.append(("mobile-ux-writer", "Text appears to be mobile UI copy"))
    if any(w in lower for w in ["chat", "bot", "assistant", "conversation", "dialog"]):
        suggestions.append(("conversational-ai-designer", "Text appears to be conversational UI"))
    if any(w in lower for w in ["translate", "localize", "i18n", "international", "language"]):
        suggestions.append(("localization-content-strategist", "Text may need localization review"))
    if any(w in lower for w in ["docs", "documentation", "api", "guide", "reference", "tutorial"]):
        suggestions.append(("technical-documentation-writer", "Text appears to be technical documentation"))
    if any(w in lower for w in ["entity", "entities", "taxonomy", "hierarchy", "structure", "contains", "belongs", "relationship", "naming", "convention"]):
        suggestions.append(("information-architect", "Text involves content structure, entities, or taxonomy"))
    if len(text) < 50:
        suggestions.append(("microcopy-review-agent", "Short text suitable for microcopy review"))

    if not suggestions:
        suggestions.append(("content-designer-generalist", "General content — start with the generalist"))

    return {
        "recommendations": [
            {"agent": slug, "reason": reason}
            for slug, reason in suggestions[:3]
        ],
    }


def _load_presets() -> list[dict[str, Any]]:
    """Load all preset YAML files."""
    import yaml
    presets = []
    if _PRESETS_DIR.exists():
        for f in sorted(_PRESETS_DIR.glob("*.yaml")):
            try:
                data = yaml.safe_load(f.read_text())
                data["slug"] = f.stem
                presets.append(data)
            except Exception:
                pass
    return presets


def _require_arg(arguments: dict[str, Any], key: str) -> Any:
    """Return the value for *key* or raise with a clear error message."""
    if key not in arguments:
        raise ValueError(f"Missing required argument: '{key}'")
    return arguments[key]


def handle_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    """Execute an MCP tool call and return the result."""
    registry = _get_registry()

    if name == "list_agents":
        tag = arguments.get("tag")
        if tag:
            agents = registry.filter_by_tag(tag)
        else:
            agents = registry.list_all()
        return [_agent_to_dict(a) for a in agents]

    elif name == "get_agent_info":
        agent_id = _require_arg(arguments, "agent")
        agent = registry.get(agent_id)
        if not agent:
            return {"error": f"Agent '{agent_id}' not found. Use list_agents to see available agents."}
        return _agent_to_dict(agent)

    elif name == "suggest_agent":
        text = _require_arg(arguments, "text")
        return _suggest_agent_for_text(text, arguments.get("context", ""))

    elif name == "score_readability":
        text = _require_arg(arguments, "text")
        result = _get_scorer().score(text)
        return result.to_dict()

    elif name == "lint_content":
        text = _require_arg(arguments, "text")
        results = _get_linter().lint(text)
        return {
            "total_issues": len(results),
            "issues": [
                {
                    "rule": r.rule,
                    "message": r.message,
                    "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity),
                    "suggestion": r.suggestion,
                }
                for r in results
            ],
        }

    elif name == "check_accessibility":
        text = _require_arg(arguments, "text")
        result = _get_a11y().check(text)
        return {
            "passed": result.passed,
            "issue_count": len(result.issues),
            "issues": [
                {
                    "rule": i.rule,
                    "message": i.message,
                    "severity": i.severity,
                    "suggestion": getattr(i, "suggestion", ""),
                }
                for i in result.issues
            ],
        }

    elif name == "score_all":
        text = _require_arg(arguments, "text")
        readability = _get_scorer().score(text).to_dict()
        lint_results = _get_linter().lint(text)
        a11y_result = _get_a11y().check(text)
        return {
            "readability": readability,
            "lint": {
                "total_issues": len(lint_results),
                "issues": [{"rule": r.rule, "message": r.message, "severity": r.severity.value if hasattr(r.severity, "value") else str(r.severity)} for r in lint_results],
            },
            "a11y": {
                "passed": a11y_result.passed,
                "issue_count": len(a11y_result.issues),
                "issues": [{"rule": i.rule, "message": i.message} for i in a11y_result.issues],
            },
        }

    elif name == "compare_text":
        before = _require_arg(arguments, "before")
        after = _require_arg(arguments, "after")
        return _get_scorer().compare(before, after)

    elif name == "validate_content":
        from runtime.constraints import validate_content as _validate
        text = _require_arg(arguments, "text")
        element_type = _require_arg(arguments, "element_type")
        platform = arguments.get("platform")
        target_language = arguments.get("target_language")
        result = _validate(text, element_type, platform=platform, target_language=target_language)
        return {
            "passed": result.passed,
            "text": text,
            "element_type": element_type,
            "violations": [
                {"rule": v.rule, "severity": v.severity, "message": v.message}
                for v in result.violations
            ],
            "error_count": len(result.errors),
            "warning_count": len(result.warnings),
        }

    elif name == "content_history":
        from runtime.versioning import ContentHistory
        action = _require_arg(arguments, "action")
        history = ContentHistory.load()

        if action == "list":
            count = arguments.get("count", 10)
            versions = history.list_recent(count)
            return [
                {
                    "id": v.id,
                    "agent": v.agent_name,
                    "input_preview": v.input_preview,
                    "output_preview": v.output_preview,
                    "timestamp": v.timestamp,
                }
                for v in versions
            ]
        elif action == "search":
            query = arguments.get("query", "")
            results = history.search(query)
            return [
                {
                    "id": v.id,
                    "agent": v.agent_name,
                    "input_preview": v.input_preview,
                    "output_preview": v.output_preview,
                }
                for v in results[-20:]
            ]
        elif action == "diff":
            version_id = arguments.get("query", "")
            diff = history.diff(version_id)
            if not diff:
                return {"error": f"Version '{version_id}' not found"}
            return diff
        elif action == "stats":
            return history.summary()
        else:
            return {"error": f"Unknown action: {action}"}

    elif name == "list_presets":
        presets = _load_presets()
        return [{"name": p.get("name", p["slug"]), "slug": p["slug"], "description": p.get("description", "")} for p in presets]

    elif name == "get_preset":
        presets = _load_presets()
        for p in presets:
            if p["slug"] == arguments["name"] or p.get("name", "").lower() == arguments["name"].lower():
                return p
        return {"error": f"Preset '{arguments['name']}' not found. Use list_presets to see available presets."}

    return {"error": f"Unknown tool: {name}"}


def handle_resource_read(uri: str) -> dict[str, Any]:
    """Read an MCP resource."""
    import yaml

    if uri == "cd-agency://agents":
        registry = _get_registry()
        agents = [_agent_to_dict(a) for a in registry.list_all()]
        return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(agents, indent=2)}]}

    elif uri == "cd-agency://decision-tree":
        decision_tree_path = Path(__file__).parent.parent / "docs" / "WHEN_TO_USE.md"
        if decision_tree_path.exists():
            text = decision_tree_path.read_text()
        else:
            text = "# Agent Decision Tree\n\nSee docs/WHEN_TO_USE.md"
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}

    elif uri == "cd-agency://presets":
        presets = _load_presets()
        return {"contents": [{"uri": uri, "mimeType": "application/json", "text": json.dumps(presets, indent=2)}]}

    return {"error": f"Unknown resource: {uri}"}


# ---------------------------------------------------------------------------
# MCP stdio transport (JSON-RPC over stdin/stdout)
# ---------------------------------------------------------------------------

SERVER_INFO = {
    "name": "cd-agency",
    "version": "0.5.0",
}

CAPABILITIES = {
    "tools": {},
    "resources": {},
}


def _send(msg: dict[str, Any]) -> None:
    """Send a JSON-RPC message to stdout."""
    line = json.dumps(msg)
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    """Handle a single JSON-RPC request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": SERVER_INFO,
                "capabilities": CAPABILITIES,
            },
        }

    elif method == "notifications/initialized":
        return None  # No response for notifications

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS},
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        try:
            result = handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                },
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps({"error": str(e)})}],
                    "isError": True,
                },
            }

    elif method == "resources/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"resources": RESOURCES},
        }

    elif method == "resources/read":
        uri = params.get("uri", "")
        result = handle_resource_read(uri)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        }

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


def run_stdio() -> None:
    """Run the MCP server using stdio transport (JSON-RPC over stdin/stdout)."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = _handle_request(request)
            if response is not None:
                _send(response)
        except json.JSONDecodeError:
            _send({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            })
        except Exception as e:
            _send({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)},
            })


if __name__ == "__main__":
    run_stdio()

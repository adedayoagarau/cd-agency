"""Tests for the MCP server tool handlers."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from mcp.server import handle_tool_call, handle_resource_read, TOOLS, RESOURCES, _handle_request


class TestToolDefinitions:
    """Verify tool schemas are well-formed."""

    def test_all_tools_have_required_fields(self):
        for tool in TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"

    def test_tool_count(self):
        assert len(TOOLS) == 12

    def test_tool_names_are_unique(self):
        names = [t["name"] for t in TOOLS]
        assert len(names) == len(set(names))


class TestListAgents:

    def test_list_all_agents(self):
        result = handle_tool_call("list_agents", {})
        assert isinstance(result, list)
        assert len(result) >= 15
        for agent in result:
            assert "name" in agent
            assert "slug" in agent
            assert "description" in agent

    def test_filter_by_tag(self):
        result = handle_tool_call("list_agents", {"tag": "errors"})
        assert isinstance(result, list)
        assert len(result) >= 1
        for agent in result:
            assert "errors" in [t.lower() for t in agent["tags"]]


class TestGetAgentInfo:

    def test_get_by_slug(self):
        result = handle_tool_call("get_agent_info", {"agent": "error-message-architect"})
        assert result["slug"] == "error-message-architect"
        assert "inputs" in result
        assert "outputs" in result

    def test_get_by_alias(self):
        result = handle_tool_call("get_agent_info", {"agent": "error"})
        assert "error" in result["slug"].lower() or "error" in result["name"].lower()

    def test_unknown_agent(self):
        result = handle_tool_call("get_agent_info", {"agent": "nonexistent-agent-xyz"})
        assert "error" in result


class TestSuggestAgent:

    def test_suggest_for_error_text(self):
        result = handle_tool_call("suggest_agent", {"text": "Error: Something went wrong"})
        slugs = [r["agent"] for r in result["recommendations"]]
        assert "error-message-architect" in slugs

    def test_suggest_for_cta_text(self):
        result = handle_tool_call("suggest_agent", {"text": "Sign up now"})
        slugs = [r["agent"] for r in result["recommendations"]]
        assert "cta-optimization-specialist" in slugs

    def test_suggest_with_context(self):
        result = handle_tool_call("suggest_agent", {"text": "Submit", "context": "button CTA"})
        assert len(result["recommendations"]) >= 1

    def test_suggest_for_generic_text(self):
        result = handle_tool_call("suggest_agent", {"text": "This is a very long paragraph about our product that explains many features and capabilities in detail."})
        assert len(result["recommendations"]) >= 1


class TestScoreReadability:

    def test_score_simple_text(self):
        result = handle_tool_call("score_readability", {"text": "Click the button. It is easy."})
        assert "flesch_reading_ease" in result
        assert "flesch_kincaid_grade" in result
        assert "word_count" in result
        assert result["word_count"] > 0

    def test_score_empty_text(self):
        result = handle_tool_call("score_readability", {"text": ""})
        assert result["word_count"] == 0


class TestLintContent:

    def test_lint_returns_structure(self):
        result = handle_tool_call("lint_content", {"text": "Click here for more information."})
        assert "total_issues" in result
        assert "issues" in result
        assert isinstance(result["issues"], list)

    def test_lint_clean_text(self):
        result = handle_tool_call("lint_content", {"text": "Save your changes."})
        assert isinstance(result["total_issues"], int)


class TestCheckAccessibility:

    def test_check_returns_structure(self):
        result = handle_tool_call("check_accessibility", {"text": "THIS IS ALL CAPS TEXT!!!"})
        assert "passed" in result
        assert "issue_count" in result
        assert "issues" in result

    def test_check_accessible_text(self):
        result = handle_tool_call("check_accessibility", {"text": "Save your work before closing."})
        assert "passed" in result


class TestScoreAll:

    def test_combined_score(self):
        result = handle_tool_call("score_all", {"text": "Click here to learn more about our product."})
        assert "readability" in result
        assert "lint" in result
        assert "a11y" in result
        assert "flesch_reading_ease" in result["readability"]
        assert "total_issues" in result["lint"]
        assert "passed" in result["a11y"]


class TestCompareText:

    def test_compare_returns_improvements(self):
        result = handle_tool_call("compare_text", {
            "before": "An error has occurred. Please try again later.",
            "after": "Something went wrong. Try again.",
        })
        assert "before" in result
        assert "after" in result
        assert "improvements" in result
        assert "word_count_change" in result["improvements"]


class TestPresets:

    def test_list_presets(self):
        result = handle_tool_call("list_presets", {})
        assert isinstance(result, list)
        assert len(result) >= 1
        for preset in result:
            assert "slug" in preset

    def test_get_preset(self):
        presets = handle_tool_call("list_presets", {})
        if presets:
            slug = presets[0]["slug"]
            result = handle_tool_call("get_preset", {"name": slug})
            assert "slug" in result

    def test_unknown_preset(self):
        result = handle_tool_call("get_preset", {"name": "nonexistent-preset-xyz"})
        assert "error" in result


class TestResources:

    def test_resource_definitions(self):
        assert len(RESOURCES) == 3
        for r in RESOURCES:
            assert "uri" in r
            assert "name" in r

    def test_read_agents_resource(self):
        result = handle_resource_read("cd-agency://agents")
        assert "contents" in result
        data = json.loads(result["contents"][0]["text"])
        assert len(data) >= 15

    def test_read_presets_resource(self):
        result = handle_resource_read("cd-agency://presets")
        assert "contents" in result

    def test_read_decision_tree_resource(self):
        result = handle_resource_read("cd-agency://decision-tree")
        assert "contents" in result

    def test_unknown_resource(self):
        result = handle_resource_read("cd-agency://nonexistent")
        assert "error" in result


class TestJsonRpcProtocol:

    def test_initialize(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        assert resp["id"] == 1
        assert "protocolVersion" in resp["result"]
        assert resp["result"]["serverInfo"]["name"] == "cd-agency"

    def test_tools_list(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })
        assert len(resp["result"]["tools"]) == 12

    def test_tools_call(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "list_agents",
                "arguments": {},
            },
        })
        content = resp["result"]["content"][0]["text"]
        data = json.loads(content)
        assert len(data) >= 15

    def test_resources_list(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/list",
            "params": {},
        })
        assert len(resp["result"]["resources"]) == 3

    def test_ping(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "ping",
        })
        assert resp["id"] == 5
        assert resp["result"] == {}

    def test_unknown_method(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "nonexistent/method",
        })
        assert "error" in resp

    def test_notification_returns_none(self):
        resp = _handle_request({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        })
        assert resp is None


class TestValidateContent:

    def test_validate_button_passes(self):
        result = handle_tool_call("validate_content", {
            "text": "Save",
            "element_type": "button",
        })
        assert result["passed"] is True
        assert result["error_count"] == 0

    def test_validate_button_too_long(self):
        result = handle_tool_call("validate_content", {
            "text": "Save all your changes and continue to the next step",
            "element_type": "button",
        })
        assert result["passed"] is False
        assert result["error_count"] >= 1

    def test_validate_with_platform(self):
        result = handle_tool_call("validate_content", {
            "text": "save changes",
            "element_type": "button",
            "platform": "ios",
        })
        assert "violations" in result
        # iOS should flag lowercase for Title Case
        assert result["warning_count"] >= 1

    def test_validate_with_localization(self):
        result = handle_tool_call("validate_content", {
            "text": "x" * 45,
            "element_type": "push_title",
            "target_language": "de",
        })
        assert any(v["rule"] == "localization_expansion" for v in result["violations"])


class TestContentHistory:

    def test_list_action(self):
        result = handle_tool_call("content_history", {"action": "list"})
        assert isinstance(result, list)

    def test_stats_action(self):
        result = handle_tool_call("content_history", {"action": "stats"})
        assert "count" in result

    def test_search_action(self):
        result = handle_tool_call("content_history", {"action": "search", "query": "test"})
        assert isinstance(result, list)

    def test_diff_not_found(self):
        result = handle_tool_call("content_history", {"action": "diff", "query": "nonexistent"})
        assert "error" in result

    def test_unknown_action(self):
        result = handle_tool_call("content_history", {"action": "invalid"})
        assert "error" in result


class TestSuggestAgentIA:

    def test_suggest_for_taxonomy_text(self):
        result = handle_tool_call("suggest_agent", {"text": "We need to define the entity hierarchy and naming conventions"})
        slugs = [r["agent"] for r in result["recommendations"]]
        assert "information-architect" in slugs


class TestUnknownTool:

    def test_unknown_tool_name(self):
        result = handle_tool_call("nonexistent_tool", {})
        assert "error" in result

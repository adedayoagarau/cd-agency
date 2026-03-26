"""Tests for the tool framework (runtime/tools/)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from runtime.tools.base import Tool, ToolResult
from runtime.tools.content_tools import (
    RunLinter,
    ScoreReadability,
    CheckAccessibility,
    CheckVoiceConsistency,
)
from runtime.tools.file_tools import ReadFile, WriteFile, ListDirectory, SearchFiles
from runtime.tools.memory_tools import RememberContext, RecallContext, RecallBrandVoice
from runtime.tools.registry import ToolRegistry, build_default_registry


# ---------------------------------------------------------------------------
# ToolResult
# ---------------------------------------------------------------------------

class TestToolResult:
    def test_success_result(self):
        r = ToolResult(success=True, data={"score": 85})
        assert r.success is True
        assert r.data == {"score": 85}
        assert r.error == ""

    def test_error_result(self):
        r = ToolResult(success=False, error="Something broke")
        assert r.success is False
        assert r.error == "Something broke"

    def test_to_dict(self):
        r = ToolResult(success=True, data="hello")
        d = r.to_dict()
        assert d["success"] is True
        assert d["data"] == "hello"
        assert "error" not in d

    def test_to_dict_with_error(self):
        r = ToolResult(success=False, error="fail")
        d = r.to_dict()
        assert d["error"] == "fail"

    def test_to_content_string_text(self):
        r = ToolResult(success=True, data="plain text")
        assert r.to_content_string() == "plain text"

    def test_to_content_string_dict(self):
        r = ToolResult(success=True, data={"key": "val"})
        s = r.to_content_string()
        assert '"key"' in s

    def test_to_content_string_error(self):
        r = ToolResult(success=False, error="oops")
        assert "oops" in r.to_content_string()


# ---------------------------------------------------------------------------
# Tool base class
# ---------------------------------------------------------------------------

class TestToolSchema:
    def test_llm_schema(self):
        tool = RunLinter()
        schema = tool.to_llm_tool_schema()
        assert schema["name"] == "run_linter"
        assert "description" in schema
        assert "input_schema" in schema
        assert schema["input_schema"]["type"] == "object"
        assert "text" in schema["input_schema"]["properties"]

    def test_openai_schema(self):
        tool = ScoreReadability()
        schema = tool.to_openai_schema()
        assert schema["type"] == "function"
        assert schema["function"]["name"] == "score_readability"


# ---------------------------------------------------------------------------
# Content tools
# ---------------------------------------------------------------------------

class TestRunLinter:
    def test_lint_clean_text(self):
        tool = RunLinter()
        result = tool.execute(text="Save your changes")
        assert result.success is True
        assert "issues_found" in result.data

    def test_lint_with_jargon(self):
        tool = RunLinter()
        result = tool.execute(text="Leverage synergy to maximize value-add")
        assert result.success is True
        assert result.data["issues_found"] > 0

    def test_lint_empty_text(self):
        tool = RunLinter()
        result = tool.execute(text="")
        assert result.success is False

    def test_lint_error_type(self):
        tool = RunLinter()
        result = tool.execute(text="Something happened.", content_type="error")
        assert result.success is True


class TestScoreReadability:
    def test_score_simple_text(self):
        tool = ScoreReadability()
        result = tool.execute(text="This is a simple sentence. It is easy to read.")
        assert result.success is True
        assert "flesch_reading_ease" in result.data
        assert result.data["flesch_reading_ease"] > 0

    def test_score_empty(self):
        tool = ScoreReadability()
        result = tool.execute(text="")
        assert result.success is False


class TestCheckAccessibility:
    def test_clean_text(self):
        tool = CheckAccessibility()
        result = tool.execute(text="Save your work before leaving this page.")
        assert result.success is True
        assert "issues" in result.data

    def test_click_here_detected(self):
        tool = CheckAccessibility()
        result = tool.execute(text="Click here to learn more about our product features and pricing.")
        assert result.success is True
        issues = result.data["issues"]
        rules = [i["rule"] for i in issues]
        assert "descriptive-link-text" in rules

    def test_custom_grade(self):
        tool = CheckAccessibility()
        result = tool.execute(text="Simple text.", target_grade=6.0)
        assert result.success is True


class TestCheckVoiceConsistency:
    def test_basic_check(self):
        tool = CheckVoiceConsistency()
        result = tool.execute(
            text="Welcome aboard! Let's get started.",
            tone_descriptors="friendly, warm",
            dont_list="formal language, corporate speak",
        )
        assert result.success is True
        assert "score" in result.data

    def test_empty_text(self):
        tool = CheckVoiceConsistency()
        result = tool.execute(text="")
        assert result.success is False


# ---------------------------------------------------------------------------
# File tools
# ---------------------------------------------------------------------------

class TestReadFile:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        tool = ReadFile(root=tmp_path)
        result = tool.execute(path="test.txt")
        assert result.success is True
        assert result.data["content"] == "hello world"

    def test_read_nonexistent(self, tmp_path):
        tool = ReadFile(root=tmp_path)
        result = tool.execute(path="nope.txt")
        assert result.success is False

    def test_read_blocked_file(self, tmp_path):
        f = tmp_path / ".env"
        f.write_text("SECRET=123")
        tool = ReadFile(root=tmp_path)
        result = tool.execute(path=".env")
        assert result.success is False
        assert "denied" in result.error.lower()

    def test_read_no_path(self, tmp_path):
        tool = ReadFile(root=tmp_path)
        result = tool.execute()
        assert result.success is False


class TestWriteFile:
    def test_write_new_file(self, tmp_path):
        tool = WriteFile(root=tmp_path)
        result = tool.execute(path="out.txt", content="hello")
        assert result.success is True
        assert (tmp_path / "out.txt").read_text() == "hello"

    def test_write_blocked_path(self, tmp_path):
        tool = WriteFile(root=tmp_path)
        result = tool.execute(path=".env", content="bad")
        assert result.success is False

    def test_write_creates_dirs(self, tmp_path):
        tool = WriteFile(root=tmp_path)
        result = tool.execute(path="sub/dir/file.txt", content="nested")
        assert result.success is True
        assert (tmp_path / "sub" / "dir" / "file.txt").exists()


class TestListDirectory:
    def test_list_root(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.md").write_text("b")
        tool = ListDirectory(root=tmp_path)
        result = tool.execute(path=".")
        assert result.success is True
        assert result.data["count"] >= 2

    def test_list_with_pattern(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.md").write_text("b")
        tool = ListDirectory(root=tmp_path)
        result = tool.execute(path=".", pattern="*.md")
        assert result.success is True
        assert result.data["count"] == 1


class TestSearchFiles:
    def test_search_found(self, tmp_path):
        (tmp_path / "hello.txt").write_text("The quick brown fox")
        tool = SearchFiles(root=tmp_path)
        result = tool.execute(pattern="quick brown")
        assert result.success is True
        assert result.data["count"] >= 1

    def test_search_not_found(self, tmp_path):
        (tmp_path / "hello.txt").write_text("nothing here")
        tool = SearchFiles(root=tmp_path)
        result = tool.execute(pattern="xyzzy")
        assert result.success is True
        assert result.data["count"] == 0

    def test_search_invalid_regex(self, tmp_path):
        tool = SearchFiles(root=tmp_path)
        result = tool.execute(pattern="[invalid")
        assert result.success is False


# ---------------------------------------------------------------------------
# Memory tools
# ---------------------------------------------------------------------------

class TestRememberContext:
    def test_remember(self, tmp_path):
        from runtime.memory import ProjectMemory

        mem = ProjectMemory(project_dir=tmp_path)
        tool = RememberContext(memory=mem)
        result = tool.execute(key="test-key", value="test-value", category="terminology")
        assert result.success is True
        assert mem.recall("test-key") is not None

    def test_remember_missing_key(self, tmp_path):
        from runtime.memory import ProjectMemory

        mem = ProjectMemory(project_dir=tmp_path)
        tool = RememberContext(memory=mem)
        result = tool.execute(key="", value="test")
        assert result.success is False


class TestRecallContext:
    def test_recall(self, tmp_path):
        from runtime.memory import ProjectMemory

        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("error-tone", "Use friendly language for errors", "voice")
        tool = RecallContext(memory=mem)
        result = tool.execute(query="error")
        assert result.success is True
        assert result.data["count"] >= 1


class TestRecallBrandVoice:
    def test_recall_voice(self, tmp_path):
        from runtime.memory import ProjectMemory

        mem = ProjectMemory(project_dir=tmp_path)
        mem.remember("voice-tone", "Warm and encouraging", "voice")
        mem.remember("term-login", "Use 'sign in' not 'login'", "terminology")
        tool = RecallBrandVoice(memory=mem)
        result = tool.execute()
        assert result.success is True
        assert result.data["total"] == 2


# ---------------------------------------------------------------------------
# Tool registry
# ---------------------------------------------------------------------------

class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = RunLinter()
        registry.register(tool)
        assert registry.get("run_linter") is tool
        assert "run_linter" in registry
        assert len(registry) == 1

    def test_get_missing(self):
        registry = ToolRegistry()
        assert registry.get("nope") is None

    def test_get_tools_by_names(self):
        registry = build_default_registry()
        tools = registry.get_tools_by_names(["run_linter", "score_readability"])
        assert len(tools) == 2

    def test_get_all_schemas(self):
        registry = build_default_registry()
        schemas = registry.get_all_schemas()
        assert len(schemas) == registry.count
        for schema in schemas:
            assert "name" in schema
            assert "description" in schema

    def test_build_default_registry(self):
        registry = build_default_registry()
        assert registry.count >= 10
        assert "run_linter" in registry
        assert "score_readability" in registry
        assert "check_accessibility" in registry
        assert "check_voice_consistency" in registry
        assert "read_file" in registry
        assert "write_file" in registry
        assert "list_directory" in registry
        assert "search_files" in registry
        assert "remember_context" in registry
        assert "recall_context" in registry
        assert "recall_brand_voice" in registry

    def test_get_tools_for_agent(self):
        registry = build_default_registry()
        tools = registry.get_tools_for_agent("error-message-architect")
        names = [t.name for t in tools]
        assert "run_linter" in names
        assert "score_readability" in names


# ---------------------------------------------------------------------------
# Loader reads tools from frontmatter
# ---------------------------------------------------------------------------

class TestLoaderToolsField:
    def test_loads_tools_from_frontmatter(self, tmp_path):
        from runtime.loader import load_agent

        md = tmp_path / "test-agent.md"
        md.write_text(
            "---\n"
            "name: Test Agent\n"
            "description: A test\n"
            "tools:\n"
            "  - run_linter\n"
            "  - score_readability\n"
            "inputs:\n"
            "  - name: content\n"
            "    type: string\n"
            "---\n"
            "### System Prompt\n"
            "You are a test agent.\n"
        )
        agent = load_agent(md)
        assert agent.available_tools == ["run_linter", "score_readability"]

    def test_missing_tools_defaults_empty(self, tmp_path):
        from runtime.loader import load_agent

        md = tmp_path / "test-agent.md"
        md.write_text(
            "---\n"
            "name: Test Agent\n"
            "description: A test\n"
            "inputs:\n"
            "  - name: content\n"
            "    type: string\n"
            "---\n"
            "### System Prompt\n"
            "You are a test agent.\n"
        )
        agent = load_agent(md)
        assert agent.available_tools == []

    def test_error_message_architect_has_tools(self):
        """Verify the updated error-message-architect loads with tools."""
        from runtime.loader import load_agent

        md_path = Path("content-design/error-message-architect.md")
        if md_path.exists():
            agent = load_agent(md_path)
            assert len(agent.available_tools) > 0
            assert "run_linter" in agent.available_tools

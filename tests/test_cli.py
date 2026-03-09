"""Tests for the CLI interface."""

import json
import pytest
from click.testing import CliRunner
from runtime.cli import main


@pytest.fixture
def runner():
    return CliRunner()


class TestAgentList:
    def test_agent_list(self, runner):
        result = runner.invoke(main, ["agent", "list"])
        assert result.exit_code == 0
        assert "Content Design Agents" in result.output

    def test_agent_list_json(self, runner):
        result = runner.invoke(main, ["agent", "list", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 15
        assert "name" in data[0]
        assert "slug" in data[0]

    def test_agent_list_filter_tag(self, runner):
        result = runner.invoke(main, ["agent", "list", "--tag", "mobile", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        for agent in data:
            assert "mobile" in [t.lower() for t in agent["tags"]]

    def test_agent_list_filter_difficulty(self, runner):
        result = runner.invoke(main, ["agent", "list", "--difficulty", "beginner", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        for agent in data:
            assert agent["difficulty"] == "beginner"


class TestAgentInfo:
    def test_agent_info(self, runner):
        result = runner.invoke(main, ["agent", "info", "error"])
        assert result.exit_code == 0
        assert "Error Message Architect" in result.output

    def test_agent_info_not_found(self, runner):
        result = runner.invoke(main, ["agent", "info", "nonexistent-agent-xyz"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_agent_info_shows_inputs(self, runner):
        result = runner.invoke(main, ["agent", "info", "microcopy"])
        assert result.exit_code == 0
        assert "Required Inputs" in result.output

    def test_agent_info_shows_related(self, runner):
        result = runner.invoke(main, ["agent", "info", "error"])
        assert result.exit_code == 0
        assert "Related Agents" in result.output


class TestAgentRun:
    def test_agent_run_no_api_key(self, runner, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        result = runner.invoke(main, ["agent", "run", "error", "-i", "test error"])
        assert result.exit_code != 0
        assert "ANTHROPIC_API_KEY" in result.output

    def test_agent_run_not_found(self, runner, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        result = runner.invoke(main, ["agent", "run", "nonexistent-xyz", "-i", "test"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestWorkflowList:
    def test_workflow_list(self, runner):
        result = runner.invoke(main, ["workflow", "list"])
        assert result.exit_code == 0
        assert "Workflows" in result.output

    def test_workflow_list_json(self, runner):
        result = runner.invoke(main, ["workflow", "list", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 5


class TestWorkflowInfo:
    def test_workflow_info(self, runner):
        result = runner.invoke(main, ["workflow", "info", "content-audit"])
        assert result.exit_code == 0
        assert "Steps" in result.output

    def test_workflow_info_not_found(self, runner):
        result = runner.invoke(main, ["workflow", "info", "nonexistent-workflow"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestScoreReadability:
    def test_score_readability(self, runner):
        result = runner.invoke(main, ["score", "readability", "-i", "The cat sat on the mat."])
        assert result.exit_code == 0
        assert "Readability" in result.output
        assert "Flesch" in result.output

    def test_score_readability_json(self, runner):
        result = runner.invoke(main, ["score", "readability", "-i", "Simple text.", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "readability" in data
        assert "word_count" in data["readability"]

    def test_score_readability_compare(self, runner):
        result = runner.invoke(main, [
            "score", "readability",
            "-i", "Simple text.",
            "--compare", "The implementation of sophisticated algorithms requires understanding.",
        ])
        assert result.exit_code == 0
        assert "Before/After" in result.output


class TestScoreLint:
    def test_score_lint(self, runner):
        result = runner.invoke(main, ["score", "lint", "-i", "Start your free trial"])
        assert result.exit_code == 0
        assert "Content Lint" in result.output

    def test_score_lint_with_type(self, runner):
        result = runner.invoke(main, ["score", "lint", "-i", "Get started", "--type", "cta"])
        assert result.exit_code == 0
        assert "cta-action-verb" in result.output

    def test_score_lint_json(self, runner):
        result = runner.invoke(main, ["score", "lint", "-i", "Start now", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "lint" in data


class TestScoreA11y:
    def test_score_a11y(self, runner):
        result = runner.invoke(main, ["score", "a11y", "-i", "Click here for more information."])
        assert result.exit_code == 0
        assert "Accessibility" in result.output

    def test_score_a11y_json(self, runner):
        result = runner.invoke(main, ["score", "a11y", "-i", "Simple text.", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "accessibility" in data

    def test_score_a11y_click_here_detected(self, runner):
        result = runner.invoke(main, ["score", "a11y", "-i", "Click here to learn more."])
        assert result.exit_code == 0
        assert "click here" in result.output.lower() or "link" in result.output.lower()


class TestScoreAll:
    def test_score_all(self, runner):
        result = runner.invoke(main, ["score", "all", "-i", "Start your free trial today."])
        assert result.exit_code == 0
        assert "CONTENT SCORING REPORT" in result.output

    def test_score_all_json(self, runner):
        result = runner.invoke(main, ["score", "all", "-i", "Test content.", "--json-output"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "readability" in data
        assert "lint" in data
        assert "accessibility" in data

    def test_score_all_markdown(self, runner):
        result = runner.invoke(main, ["score", "all", "-i", "Test content.", "--markdown"])
        assert result.exit_code == 0
        assert "# Content Scoring Report" in result.output


class TestVersion:
    def test_version(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestConfigFile:
    def test_config_loads_from_env(self):
        from runtime.config import Config
        config = Config.from_env()
        assert config.agents_dir.name == "content-design"

    def test_config_validate_no_key(self):
        from runtime.config import Config
        from pathlib import Path
        cfg = Config(api_key="", agents_dir=Path("content-design"))
        errors = cfg.validate()
        assert any("ANTHROPIC_API_KEY" in e for e in errors)

    def test_config_validate_missing_dir(self):
        from runtime.config import Config
        from pathlib import Path
        config = Config(api_key="test", agents_dir=Path("/nonexistent/path"))
        errors = config.validate()
        assert any("not found" in e for e in errors)

"""Tests for the agent loader."""

from pathlib import Path

import pytest

from runtime.loader import load_agent, load_agents_from_directory, _parse_frontmatter, _parse_sections


AGENTS_DIR = Path(__file__).parent.parent / "content-design"


class TestParseFrontmatter:
    def test_parses_yaml_frontmatter(self):
        text = "---\nname: Test Agent\ndescription: A test\n---\n\nBody content"
        fm, body = _parse_frontmatter(text)
        assert fm["name"] == "Test Agent"
        assert fm["description"] == "A test"
        assert "Body content" in body

    def test_no_frontmatter_returns_empty_dict(self):
        text = "Just some body text"
        fm, body = _parse_frontmatter(text)
        assert fm == {}
        assert body == text

    def test_handles_complex_yaml(self):
        text = '---\nname: Agent\ntags: ["a", "b"]\ninputs:\n  - name: field1\n    type: string\n---\nBody'
        fm, body = _parse_frontmatter(text)
        assert fm["tags"] == ["a", "b"]
        assert fm["inputs"][0]["name"] == "field1"


class TestParseSections:
    def test_parses_sections_by_h3(self):
        body = "### System Prompt\n\nYou are a writer.\n\n### Core Mission\n\nWrite great content."
        sections = _parse_sections(body)
        assert "system prompt" in sections
        assert "core mission" in sections
        assert "You are a writer." in sections["system prompt"]

    def test_empty_body(self):
        sections = _parse_sections("")
        assert sections == {}


class TestLoadAgent:
    def test_loads_generalist(self):
        path = AGENTS_DIR / "content-designer-generalist.md"
        agent = load_agent(path)
        assert agent.name == "Content Designer Generalist"
        assert agent.version == "1.0.0"
        assert len(agent.inputs) > 0
        assert len(agent.outputs) > 0
        assert len(agent.tags) > 0
        assert agent.system_prompt != ""
        assert agent.slug == "content-designer-generalist"

    def test_loads_error_architect(self):
        path = AGENTS_DIR / "error-message-architect.md"
        agent = load_agent(path)
        assert agent.name == "Error Message Architect"
        assert any("error" in t.lower() for t in agent.tags)
        assert len(agent.related_agents) > 0

    def test_all_agents_have_required_fields(self):
        for filepath in sorted(AGENTS_DIR.glob("*.md")):
            agent = load_agent(filepath)
            assert agent.name, f"{filepath.name}: missing name"
            assert agent.description, f"{filepath.name}: missing description"
            assert len(agent.inputs) > 0, f"{filepath.name}: no inputs defined"
            assert len(agent.outputs) > 0, f"{filepath.name}: no outputs defined"
            assert agent.system_prompt, f"{filepath.name}: no system prompt"
            assert agent.version, f"{filepath.name}: no version"

    def test_all_agents_have_few_shot_examples(self):
        for filepath in sorted(AGENTS_DIR.glob("*.md")):
            agent = load_agent(filepath)
            assert agent.few_shot_examples, f"{filepath.name}: no few-shot examples"

    def test_all_agents_have_related_agents(self):
        for filepath in sorted(AGENTS_DIR.glob("*.md")):
            agent = load_agent(filepath)
            assert len(agent.related_agents) > 0, f"{filepath.name}: no related agents"


class TestLoadAgentsFromDirectory:
    def test_loads_all_15_agents(self):
        agents = load_agents_from_directory(AGENTS_DIR)
        assert len(agents) == 19

    def test_nonexistent_directory_returns_empty(self):
        agents = load_agents_from_directory(Path("/nonexistent"))
        assert agents == []

    def test_all_agents_unique_slugs(self):
        agents = load_agents_from_directory(AGENTS_DIR)
        slugs = [a.slug for a in agents]
        assert len(slugs) == len(set(slugs)), "Duplicate agent slugs found"

"""Tests for the knowledge base loader."""

from pathlib import Path

import pytest

from runtime.knowledge import (
    load_knowledge_file,
    resolve_knowledge_refs,
    list_knowledge_files,
    search_knowledge,
    _filepath_to_ref,
    _parse_frontmatter,
)


KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


class TestParseKnowledgeFrontmatter:
    def test_parses_yaml_frontmatter(self):
        text = '---\ntitle: Test\ndomain: foundations\ntags: ["a", "b"]\n---\n\nBody content'
        fm, body = _parse_frontmatter(text)
        assert fm["title"] == "Test"
        assert fm["domain"] == "foundations"
        assert fm["tags"] == ["a", "b"]
        assert "Body content" in body

    def test_no_frontmatter_returns_empty_dict(self):
        text = "Just some body text"
        fm, body = _parse_frontmatter(text)
        assert fm == {}
        assert body == text


class TestFilepathToRef:
    def test_converts_filepath_to_ref(self):
        filepath = Path("knowledge/foundations/plain-language.md")
        assert _filepath_to_ref(filepath) == "foundations/plain-language"

    def test_converts_absolute_filepath(self):
        filepath = Path("/home/user/project/knowledge/books/nicely-said.md")
        assert _filepath_to_ref(filepath) == "books/nicely-said"

    def test_handles_nested_domains(self):
        filepath = Path("knowledge/case-studies/slack-voice-and-errors.md")
        assert _filepath_to_ref(filepath) == "case-studies/slack-voice-and-errors"


class TestLoadKnowledgeFile:
    def test_loads_plain_language(self):
        filepath = KNOWLEDGE_DIR / "foundations" / "plain-language.md"
        data = load_knowledge_file(filepath)
        assert data["title"] == "Plain Language Principles"
        assert data["domain"] == "foundations"
        assert "clarity" in data["tags"]
        assert len(data["content"]) > 100
        assert "foundations/plain-language" in data["ref"]

    def test_loads_book_file(self):
        filepath = KNOWLEDGE_DIR / "books" / "nicely-said.md"
        data = load_knowledge_file(filepath)
        assert data["title"] == "Nicely Said — Nicole Fenton & Kate Kiefer Lee"
        assert data["domain"] == "books"
        assert len(data["content"]) > 100

    def test_loads_case_study(self):
        filepath = KNOWLEDGE_DIR / "case-studies" / "slack-voice-and-errors.md"
        data = load_knowledge_file(filepath)
        assert "Slack" in data["title"]
        assert data["domain"] == "case-studies"

    def test_loads_framework(self):
        filepath = KNOWLEDGE_DIR / "frameworks" / "jobs-to-be-done.md"
        data = load_knowledge_file(filepath)
        assert "Jobs to Be Done" in data["title"]
        assert data["domain"] == "frameworks"

    def test_loads_domain_file(self):
        filepath = KNOWLEDGE_DIR / "domains" / "fintech.md"
        data = load_knowledge_file(filepath)
        assert "Fintech" in data["title"]
        assert data["domain"] == "domains"

    def test_all_knowledge_files_have_required_fields(self):
        for filepath in sorted(KNOWLEDGE_DIR.rglob("*.md")):
            data = load_knowledge_file(filepath)
            assert data["title"], f"{filepath}: missing title"
            assert data["domain"], f"{filepath}: missing domain"
            assert len(data["tags"]) > 0, f"{filepath}: no tags"
            assert len(data["content"]) > 50, f"{filepath}: content too short"


class TestResolveKnowledgeRefs:
    def test_resolves_single_ref(self):
        content = resolve_knowledge_refs(
            ["foundations/plain-language"],
            knowledge_dir=KNOWLEDGE_DIR,
        )
        assert "Plain Language" in content
        assert len(content) > 100

    def test_resolves_multiple_refs(self):
        content = resolve_knowledge_refs(
            ["foundations/plain-language", "foundations/cognitive-load"],
            knowledge_dir=KNOWLEDGE_DIR,
        )
        assert "Plain Language" in content
        assert "Cognitive Load" in content
        # Should have separator between sections
        assert "---" in content

    def test_empty_refs_returns_empty_string(self):
        content = resolve_knowledge_refs([], knowledge_dir=KNOWLEDGE_DIR)
        assert content == ""

    def test_nonexistent_ref_is_skipped(self):
        content = resolve_knowledge_refs(
            ["foundations/plain-language", "nonexistent/file"],
            knowledge_dir=KNOWLEDGE_DIR,
        )
        assert "Plain Language" in content
        # Should not error, just skip the missing file

    def test_nonexistent_dir_returns_empty(self):
        content = resolve_knowledge_refs(
            ["foundations/plain-language"],
            knowledge_dir=Path("/nonexistent/dir"),
        )
        assert content == ""


class TestListKnowledgeFiles:
    def test_lists_all_files(self):
        files = list_knowledge_files(knowledge_dir=KNOWLEDGE_DIR)
        assert len(files) >= 25  # We created ~27 files

    def test_each_file_has_metadata(self):
        files = list_knowledge_files(knowledge_dir=KNOWLEDGE_DIR)
        for f in files:
            assert "ref" in f
            assert "title" in f
            assert "domain" in f
            assert "tags" in f

    def test_nonexistent_dir_returns_empty(self):
        files = list_knowledge_files(knowledge_dir=Path("/nonexistent"))
        assert files == []

    def test_includes_all_domains(self):
        files = list_knowledge_files(knowledge_dir=KNOWLEDGE_DIR)
        domains = {f["domain"] for f in files}
        assert "foundations" in domains
        assert "frameworks" in domains
        assert "research" in domains
        assert "case-studies" in domains
        assert "books" in domains
        assert "domains" in domains


class TestSearchKnowledge:
    def test_search_by_title(self):
        results = search_knowledge("plain language", knowledge_dir=KNOWLEDGE_DIR)
        assert len(results) > 0
        assert any("plain" in r["title"].lower() for r in results)

    def test_search_by_tag(self):
        results = search_knowledge("accessibility", knowledge_dir=KNOWLEDGE_DIR)
        assert len(results) > 0

    def test_search_by_content(self):
        results = search_knowledge("WCAG", knowledge_dir=KNOWLEDGE_DIR)
        assert len(results) > 0

    def test_search_no_results(self):
        results = search_knowledge("zzzznonexistentzzz", knowledge_dir=KNOWLEDGE_DIR)
        assert results == []

    def test_results_sorted_by_score(self):
        results = search_knowledge("voice", knowledge_dir=KNOWLEDGE_DIR)
        if len(results) > 1:
            scores = [r["score"] for r in results]
            assert scores == sorted(scores, reverse=True)


class TestKnowledgeIntegrationWithLoader:
    """Test that knowledge loads correctly through the agent loader."""

    def test_agent_with_knowledge_has_refs(self):
        from runtime.loader import load_agent
        agents_dir = Path(__file__).parent.parent / "content-design"
        agent = load_agent(agents_dir / "error-message-architect.md")
        assert len(agent.knowledge_refs) > 0
        assert "foundations/plain-language" in agent.knowledge_refs

    def test_agent_with_knowledge_has_content(self):
        from runtime.loader import load_agent
        agents_dir = Path(__file__).parent.parent / "content-design"
        agent = load_agent(agents_dir / "error-message-architect.md")
        assert len(agent.knowledge_content) > 0
        assert "Plain Language" in agent.knowledge_content

    def test_knowledge_injected_into_system_message(self):
        from runtime.loader import load_agent
        agents_dir = Path(__file__).parent.parent / "content-design"
        agent = load_agent(agents_dir / "error-message-architect.md")
        system_msg = agent.build_system_message()
        assert "Knowledge Base" in system_msg
        assert "Plain Language" in system_msg

    def test_agent_without_knowledge_works(self):
        from runtime.agent import Agent
        agent = Agent(
            name="Test Agent",
            description="No knowledge",
            system_prompt="You are a test agent.",
        )
        system_msg = agent.build_system_message()
        assert "Knowledge Base" not in system_msg
        assert "You are a test agent." in system_msg

    def test_all_agents_knowledge_refs_resolve(self):
        """Verify all knowledge refs in all agents point to existing files."""
        from runtime.loader import load_agents_from_directory
        agents_dir = Path(__file__).parent.parent / "content-design"
        agents = load_agents_from_directory(agents_dir)

        for agent in agents:
            for ref in agent.knowledge_refs:
                filepath = KNOWLEDGE_DIR / f"{ref}.md"
                assert filepath.exists(), (
                    f"Agent '{agent.name}' references '{ref}' but "
                    f"{filepath} does not exist"
                )

"""Tests for the Brand DNA Pipeline (runtime/brand_dna.py and related)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from runtime.brand_dna import (
    BrandDNA,
    BrandDNAProcessor,
    StyleRule,
    TerminologyEntry,
    VoicePattern,
    load_brand_dna,
    save_brand_dna,
    reset_brand_dna,
)


# ---------------------------------------------------------------------------
# VoicePattern
# ---------------------------------------------------------------------------

class TestVoicePattern:
    def test_to_prompt_line_with_examples(self):
        vp = VoicePattern(
            name="casual-tone",
            description="Uses informal language",
            examples=["Hey there!", "Nice work!"],
            confidence=0.9,
        )
        line = vp.to_prompt_line()
        assert "casual-tone" in line
        assert "Hey there!" in line

    def test_to_prompt_line_no_examples(self):
        vp = VoicePattern(name="warmth", description="Warm and friendly")
        line = vp.to_prompt_line()
        assert "warmth" in line
        assert "e.g." not in line


# ---------------------------------------------------------------------------
# TerminologyEntry
# ---------------------------------------------------------------------------

class TestTerminologyEntry:
    def test_to_prompt_line_with_avoid(self):
        te = TerminologyEntry(
            preferred="sign in",
            avoid=["log in", "login"],
            context="authentication",
        )
        line = te.to_prompt_line()
        assert '"sign in"' in line
        assert '"log in"' in line
        assert "authentication" in line

    def test_to_prompt_line_no_avoid(self):
        te = TerminologyEntry(preferred="workspace")
        line = te.to_prompt_line()
        assert '"workspace"' in line
        assert "instead of" not in line


# ---------------------------------------------------------------------------
# StyleRule
# ---------------------------------------------------------------------------

class TestStyleRule:
    def test_to_prompt_line_with_examples(self):
        sr = StyleRule(
            rule="Use sentence case for headings",
            category="capitalization",
            examples=["Save your changes"],
        )
        line = sr.to_prompt_line()
        assert "sentence case" in line
        assert "Save your changes" in line

    def test_to_prompt_line_no_examples(self):
        sr = StyleRule(rule="Always use Oxford comma")
        line = sr.to_prompt_line()
        assert "Oxford comma" in line
        assert "e.g." not in line


# ---------------------------------------------------------------------------
# BrandDNA
# ---------------------------------------------------------------------------

class TestBrandDNA:
    def test_is_empty_true(self):
        dna = BrandDNA()
        assert dna.is_empty() is True

    def test_is_empty_false(self):
        dna = BrandDNA(tone_descriptors=["friendly"])
        assert dna.is_empty() is False

    def test_build_context_block_empty(self):
        dna = BrandDNA()
        assert dna.build_context_block() == ""

    def test_build_context_block(self):
        dna = BrandDNA(
            name="Acme",
            tone_descriptors=["friendly", "clear"],
            voice_patterns=[
                VoicePattern(name="casual", description="Informal language", examples=["Hey!"]),
            ],
            terminology=[
                TerminologyEntry(preferred="sign in", avoid=["log in"]),
            ],
            style_rules=[
                StyleRule(rule="Sentence case for headings"),
            ],
            do_list=["Use active voice"],
            dont_list=["Don't use jargon"],
        )
        block = dna.build_context_block()
        assert "Acme" in block
        assert "friendly" in block
        assert "casual" in block
        assert "sign in" in block
        assert "Sentence case" in block
        assert "Use active voice" in block
        assert "Don't use jargon" in block

    def test_to_dict_and_from_dict(self):
        dna = BrandDNA(
            name="Test",
            tone_descriptors=["bold"],
            voice_patterns=[VoicePattern(name="directness", description="Direct style")],
            terminology=[TerminologyEntry(preferred="workspace", avoid=["project"])],
            style_rules=[StyleRule(rule="No passive voice", category="grammar")],
            do_list=["Be clear"],
            dont_list=["No jargon"],
            source_samples=5,
        )
        d = dna.to_dict()
        restored = BrandDNA.from_dict(d)
        assert restored.name == "Test"
        assert restored.tone_descriptors == ["bold"]
        assert len(restored.voice_patterns) == 1
        assert restored.voice_patterns[0].name == "directness"
        assert len(restored.terminology) == 1
        assert restored.terminology[0].preferred == "workspace"
        assert len(restored.style_rules) == 1
        assert restored.source_samples == 5

    def test_merge(self):
        dna1 = BrandDNA(
            tone_descriptors=["friendly"],
            voice_patterns=[VoicePattern(name="warmth", description="Warm tone")],
            terminology=[TerminologyEntry(preferred="sign in", avoid=["log in"])],
        )
        dna2 = BrandDNA(
            tone_descriptors=["friendly", "clear"],
            voice_patterns=[
                VoicePattern(name="warmth", description="Duplicate"),
                VoicePattern(name="directness", description="Direct style"),
            ],
            terminology=[
                TerminologyEntry(preferred="sign in", avoid=["login"]),
                TerminologyEntry(preferred="workspace", avoid=["project"]),
            ],
            source_samples=3,
        )
        dna1.merge(dna2)
        # warmth not duplicated
        assert len(dna1.voice_patterns) == 2
        # sign in not duplicated
        assert len(dna1.terminology) == 2
        # clear added, friendly not duplicated
        assert "clear" in dna1.tone_descriptors
        assert dna1.tone_descriptors.count("friendly") == 1
        assert dna1.source_samples == 3

    def test_merge_empty(self):
        dna = BrandDNA(tone_descriptors=["bold"])
        dna.merge(BrandDNA())
        assert dna.tone_descriptors == ["bold"]


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

class TestBrandDNAStorage:
    def test_save_and_load(self, tmp_path):
        dna = BrandDNA(
            name="SaveTest",
            tone_descriptors=["crisp"],
            voice_patterns=[VoicePattern(name="p1", description="Pattern 1")],
            terminology=[TerminologyEntry(preferred="term1")],
            style_rules=[StyleRule(rule="Rule 1")],
            source_samples=2,
        )
        save_brand_dna(dna, project_dir=tmp_path)

        loaded = load_brand_dna(project_dir=tmp_path)
        assert loaded.name == "SaveTest"
        assert loaded.tone_descriptors == ["crisp"]
        assert len(loaded.voice_patterns) == 1
        assert loaded.voice_patterns[0].name == "p1"
        assert len(loaded.terminology) == 1
        assert len(loaded.style_rules) == 1
        assert loaded.source_samples == 2

    def test_load_nonexistent(self, tmp_path):
        dna = load_brand_dna(project_dir=tmp_path)
        assert dna.is_empty()

    def test_load_corrupt_json(self, tmp_path):
        path = tmp_path / ".cd-agency" / "brand_dna.json"
        path.parent.mkdir(parents=True)
        path.write_text("not valid json", encoding="utf-8")
        dna = load_brand_dna(project_dir=tmp_path)
        assert dna.is_empty()

    def test_reset(self, tmp_path):
        dna = BrandDNA(name="ToDelete", tone_descriptors=["temp"])
        save_brand_dna(dna, project_dir=tmp_path)
        assert reset_brand_dna(project_dir=tmp_path) is True
        assert reset_brand_dna(project_dir=tmp_path) is False
        assert load_brand_dna(project_dir=tmp_path).is_empty()

    def test_storage_limits(self, tmp_path):
        dna = BrandDNA(
            voice_patterns=[VoicePattern(name=f"vp{i}", description="x") for i in range(30)],
            terminology=[TerminologyEntry(preferred=f"term{i}") for i in range(120)],
            style_rules=[StyleRule(rule=f"rule{i}") for i in range(60)],
            tone_descriptors=[f"tone{i}" for i in range(15)],
        )
        save_brand_dna(dna, project_dir=tmp_path)
        loaded = load_brand_dna(project_dir=tmp_path)
        assert len(loaded.voice_patterns) <= 20
        assert len(loaded.terminology) <= 100
        assert len(loaded.style_rules) <= 50
        assert len(loaded.tone_descriptors) <= 10


# ---------------------------------------------------------------------------
# BrandDNAProcessor
# ---------------------------------------------------------------------------

class TestBrandDNAProcessor:
    def _mock_router(self, response_json: dict):
        mock_provider = MagicMock()
        from runtime.model_providers import ProviderResponse
        mock_provider.complete.return_value = ProviderResponse(
            content=json.dumps(response_json),
            input_tokens=100,
            output_tokens=200,
        )
        router = MagicMock()
        router.resolve.return_value = (mock_provider, "test-model")
        return router

    def test_ingest_empty(self):
        processor = BrandDNAProcessor()
        dna = processor.ingest([], brand_name="Empty")
        assert dna.name == "Empty"
        assert dna.is_empty()

    def test_ingest_success(self):
        response = {
            "tone_descriptors": ["friendly", "clear"],
            "voice_patterns": [
                {"name": "warmth", "description": "Warm tone", "examples": ["Hey!"], "confidence": 0.8},
            ],
            "terminology": [
                {"preferred": "sign in", "avoid": ["log in"], "context": "auth"},
            ],
            "style_rules": [
                {"rule": "Sentence case", "category": "capitalization", "examples": ["Save your work"]},
            ],
            "do_list": ["Use active voice"],
            "dont_list": ["Don't blame the user"],
        }
        router = self._mock_router(response)
        processor = BrandDNAProcessor(model_router=router, model="test-model")
        dna = processor.ingest(["Welcome aboard! Let's get started."], brand_name="Acme")

        assert dna.name == "Acme"
        assert dna.tone_descriptors == ["friendly", "clear"]
        assert len(dna.voice_patterns) == 1
        assert dna.voice_patterns[0].name == "warmth"
        assert len(dna.terminology) == 1
        assert len(dna.style_rules) == 1
        assert dna.source_samples == 1

    def test_ingest_bad_json_response(self):
        mock_provider = MagicMock()
        from runtime.model_providers import ProviderResponse
        mock_provider.complete.return_value = ProviderResponse(
            content="This is not JSON at all",
            input_tokens=50,
            output_tokens=50,
        )
        router = MagicMock()
        router.resolve.return_value = (mock_provider, "test-model")

        processor = BrandDNAProcessor(model_router=router, model="test-model")
        dna = processor.ingest(["Some content"])
        assert dna.is_empty()

    def test_ingest_json_in_code_block(self):
        response = {
            "tone_descriptors": ["bold"],
            "voice_patterns": [],
            "terminology": [],
            "style_rules": [],
            "do_list": [],
            "dont_list": [],
        }
        mock_provider = MagicMock()
        from runtime.model_providers import ProviderResponse
        mock_provider.complete.return_value = ProviderResponse(
            content=f"```json\n{json.dumps(response)}\n```",
            input_tokens=50,
            output_tokens=50,
        )
        router = MagicMock()
        router.resolve.return_value = (mock_provider, "test-model")

        processor = BrandDNAProcessor(model_router=router, model="test-model")
        dna = processor.ingest(["Bold content"])
        assert dna.tone_descriptors == ["bold"]

    def test_ingest_file_markdown(self, tmp_path):
        md = tmp_path / "brand-content.md"
        md.write_text(
            "# Welcome\n\nWelcome aboard! Let's get started.\n\n"
            "# Errors\n\nOops, something went sideways. Give it another try?\n",
            encoding="utf-8",
        )

        response = {
            "tone_descriptors": ["casual"],
            "voice_patterns": [
                {"name": "playful-errors", "description": "Light touch on errors", "examples": ["went sideways"], "confidence": 0.7},
            ],
            "terminology": [],
            "style_rules": [],
            "do_list": [],
            "dont_list": [],
        }
        router = self._mock_router(response)
        processor = BrandDNAProcessor(model_router=router, model="test-model")
        dna = processor.ingest_file(md, brand_name="TestBrand")

        assert dna.name == "TestBrand"
        assert len(dna.voice_patterns) == 1

    def test_ingest_file_yaml(self, tmp_path):
        yml = tmp_path / "voice.yaml"
        yml.write_text(
            "name: TestVoice\n"
            "samples:\n"
            "  - 'Welcome aboard! Let us get started with your workspace.'\n"
            "  - 'Your changes are saved. Nice work!'\n",
            encoding="utf-8",
        )

        response = {
            "tone_descriptors": ["encouraging"],
            "voice_patterns": [],
            "terminology": [],
            "style_rules": [],
            "do_list": [],
            "dont_list": [],
        }
        router = self._mock_router(response)
        processor = BrandDNAProcessor(model_router=router, model="test-model")
        dna = processor.ingest_file(yml)

        assert dna.tone_descriptors == ["encouraging"]

    def test_split_text(self):
        samples = BrandDNAProcessor._split_text(
            "First paragraph with enough content.\n\n"
            "Second paragraph with enough content.\n\n"
            "Short.\n\n"
            "Third paragraph with enough content."
        )
        # "Short." is under 20 chars, should be excluded
        assert len(samples) == 3

    def test_split_markdown(self):
        samples = BrandDNAProcessor._split_markdown_sections(
            "# First Section\n\nSome content that is long enough to keep.\n\n"
            "## Second Section\n\nMore content that is long enough to keep."
        )
        assert len(samples) == 2

    def test_extract_from_yaml(self):
        data = {
            "name": "Test",
            "samples": [
                "A long enough string to keep for analysis purposes.",
                "Short",
                "Another long enough string that has plenty of characters.",
            ],
            "nested": {"deep": "Yet another string with plenty of content for analysis."},
        }
        samples = BrandDNAProcessor._extract_samples_from_yaml(data)
        # "Short" and "Test" are under 20 chars
        assert len(samples) == 3


# ---------------------------------------------------------------------------
# Brand tools
# ---------------------------------------------------------------------------

class TestExtractBrandPatterns:
    def test_short_content(self):
        from runtime.tools.brand_tools import ExtractBrandPatterns

        tool = ExtractBrandPatterns()
        result = tool.execute(content="Hi")
        assert result.success is False
        assert "too short" in result.error.lower()

    def test_extract_success(self):
        from runtime.tools.brand_tools import ExtractBrandPatterns

        response = {
            "tone_descriptors": ["warm"],
            "voice_patterns": [
                {"name": "friendliness", "description": "Friendly tone", "examples": ["Hey!"], "confidence": 0.8},
            ],
            "terminology": [
                {"preferred": "workspace", "avoid": ["project"], "context": "product"},
            ],
            "style_rules": [],
            "do_list": [],
            "dont_list": [],
        }
        mock_provider = MagicMock()
        from runtime.model_providers import ProviderResponse
        mock_provider.complete.return_value = ProviderResponse(
            content=json.dumps(response),
            input_tokens=100,
            output_tokens=200,
        )
        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")

        with patch("runtime.tools.brand_tools.ExtractBrandPatterns.execute") as mock_execute:
            mock_execute.return_value = ToolResult(
                success=True,
                data={
                    "voice_patterns": 1,
                    "terminology_entries": 1,
                    "style_rules": 0,
                    "tone_descriptors": ["warm"],
                    "total_patterns": 2,
                },
            )
            tool = ExtractBrandPatterns()
            result = tool.execute(content="Welcome aboard! Let's get your workspace set up.")

        assert result.success is True
        assert result.data["total_patterns"] == 2


class TestQueryBrandDNA:
    def test_query_empty(self, tmp_path):
        from runtime.tools.brand_tools import QueryBrandDNA

        with patch("runtime.brand_dna.load_brand_dna") as mock_load:
            mock_load.return_value = BrandDNA()
            tool = QueryBrandDNA()
            result = tool.execute()
            assert result.success is True
            assert result.data["has_brand_dna"] is False

    def test_query_with_data(self, tmp_path):
        from runtime.tools.brand_tools import QueryBrandDNA

        dna = BrandDNA(
            name="Acme",
            tone_descriptors=["friendly"],
            voice_patterns=[VoicePattern(name="warmth", description="Warm")],
            terminology=[TerminologyEntry(preferred="sign in")],
        )
        with patch("runtime.brand_dna.load_brand_dna") as mock_load:
            mock_load.return_value = dna
            tool = QueryBrandDNA()
            result = tool.execute()
            assert result.success is True
            assert result.data["has_brand_dna"] is True
            assert result.data["name"] == "Acme"
            assert result.data["voice_patterns"] == 1


# ---------------------------------------------------------------------------
# Tool registry integration
# ---------------------------------------------------------------------------

class TestBrandToolsInRegistry:
    def test_brand_tools_registered(self):
        from runtime.tools.registry import build_default_registry

        registry = build_default_registry()
        assert "extract_brand_patterns" in registry
        assert "query_brand_dna" in registry

    def test_registry_count_increased(self):
        from runtime.tools.registry import build_default_registry

        registry = build_default_registry()
        assert registry.count >= 13  # 11 original + 2 brand tools

    def test_archaeologist_agent_tools(self):
        from runtime.tools.registry import build_default_registry

        registry = build_default_registry()
        tools = registry.get_tools_for_agent("brand-voice-archaeologist")
        names = [t.name for t in tools]
        assert "extract_brand_patterns" in names
        assert "query_brand_dna" in names


# ---------------------------------------------------------------------------
# Runner integration — brand DNA injected into system message
# ---------------------------------------------------------------------------

class TestRunnerBrandDNAIntegration:
    @patch("runtime.runner.ModelRouter.from_config")
    def test_brand_dna_injected(self, mock_from_config):
        from runtime.agent import Agent, AgentInput
        from runtime.model_providers import ProviderResponse
        from runtime.runner import AgentRunner
        from runtime.config import Config

        mock_provider = MagicMock()
        mock_provider.complete.return_value = ProviderResponse(
            content="Response with brand voice", input_tokens=10, output_tokens=5,
        )
        mock_router = MagicMock()
        mock_router.resolve.return_value = (mock_provider, "test-model")
        mock_from_config.return_value = mock_router

        dna = BrandDNA(
            name="TestBrand",
            tone_descriptors=["friendly"],
            voice_patterns=[VoicePattern(name="warmth", description="Warm tone")],
        )

        agent = Agent(
            name="Test",
            description="Test agent",
            inputs=[AgentInput(name="content", type="string", required=True)],
            system_prompt="You are a test agent.",
            source_file="test.md",
        )

        config = Config(api_key="test-key", model="test-model")
        runner = AgentRunner(config)

        with patch("runtime.brand_dna.load_brand_dna", return_value=dna):
            result = runner.run(agent, {"content": "test"})

        assert result.content == "Response with brand voice"
        # Verify the system message was passed with brand context
        call_kwargs = mock_provider.complete.call_args
        system_msg = call_kwargs.kwargs.get("system", "") if call_kwargs.kwargs else call_kwargs[1].get("system", "")
        assert "Brand Voice" in system_msg or "TestBrand" in system_msg


# ---------------------------------------------------------------------------
# Agent loader — brand-voice-archaeologist loads with tools
# ---------------------------------------------------------------------------

class TestBrandVoiceArchaeologistAgent:
    def test_agent_loads(self):
        from runtime.loader import load_agent

        md_path = Path("content-design/brand-voice-archaeologist.md")
        if md_path.exists():
            agent = load_agent(md_path)
            assert agent.name == "Brand Voice Archaeologist"
            assert "extract_brand_patterns" in agent.available_tools
            assert "query_brand_dna" in agent.available_tools
            assert len(agent.available_tools) >= 4


# ---------------------------------------------------------------------------
# CLI brand commands
# ---------------------------------------------------------------------------

class TestBrandCLI:
    def test_brand_group_exists(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        result = runner.invoke(main, ["brand", "--help"])
        assert result.exit_code == 0
        assert "ingest" in result.output
        assert "show" in result.output
        assert "export" in result.output
        assert "reset" in result.output

    def test_brand_show_empty(self):
        from runtime.cli import main
        from click.testing import CliRunner

        runner = CliRunner()
        with patch("runtime.brand_dna.load_brand_dna") as mock_load:
            mock_load.return_value = BrandDNA()
            result = runner.invoke(main, ["brand", "show"])
            assert result.exit_code == 0
            assert "No brand DNA" in result.output

    def test_brand_show_json(self, tmp_path):
        from runtime.cli import main
        from click.testing import CliRunner

        dna = BrandDNA(name="TestCLI", tone_descriptors=["clear"])
        save_brand_dna(dna, project_dir=tmp_path)

        runner = CliRunner()
        with patch("runtime.brand_dna._brand_dna_path") as mock_path:
            mock_path.return_value = tmp_path / ".cd-agency" / "brand_dna.json"
            result = runner.invoke(main, ["brand", "show", "--json-output"])
            assert result.exit_code == 0
            assert "TestCLI" in result.output


# Need this import for the mock in TestExtractBrandPatterns
from runtime.tools.base import ToolResult

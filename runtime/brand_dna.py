"""Brand DNA — data models and processor for learning brand voice from content.

Ingests existing content samples, extracts voice patterns, terminology
preferences, and style rules, then stores them for automatic injection
into agent prompts.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class VoicePattern:
    """A detected voice/tone pattern from brand content."""

    name: str
    description: str
    examples: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0–1.0

    def to_prompt_line(self) -> str:
        ex = "; ".join(f'"{e}"' for e in self.examples[:3])
        return f"- **{self.name}**: {self.description} (e.g. {ex})" if ex else f"- **{self.name}**: {self.description}"


@dataclass
class TerminologyEntry:
    """A preferred/avoided term mapping."""

    preferred: str
    avoid: list[str] = field(default_factory=list)
    context: str = ""

    def to_prompt_line(self) -> str:
        avoid_str = ", ".join(f'"{a}"' for a in self.avoid)
        line = f'- Use "{self.preferred}"'
        if avoid_str:
            line += f" instead of {avoid_str}"
        if self.context:
            line += f" ({self.context})"
        return line


@dataclass
class StyleRule:
    """A writing style rule extracted from brand content."""

    rule: str
    category: str = ""  # punctuation, capitalization, formatting, structure
    examples: list[str] = field(default_factory=list)

    def to_prompt_line(self) -> str:
        ex = "; ".join(f'"{e}"' for e in self.examples[:2])
        return f"- {self.rule} (e.g. {ex})" if ex else f"- {self.rule}"


@dataclass
class BrandDNA:
    """Complete brand voice profile extracted from content samples."""

    name: str = ""
    voice_patterns: list[VoicePattern] = field(default_factory=list)
    terminology: list[TerminologyEntry] = field(default_factory=list)
    style_rules: list[StyleRule] = field(default_factory=list)
    tone_descriptors: list[str] = field(default_factory=list)
    do_list: list[str] = field(default_factory=list)
    dont_list: list[str] = field(default_factory=list)
    source_samples: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self) -> None:
        now = time.time()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def is_empty(self) -> bool:
        return not (self.voice_patterns or self.terminology or self.style_rules
                    or self.tone_descriptors)

    def build_context_block(self) -> str:
        """Build a prompt context block from the brand DNA."""
        if self.is_empty():
            return ""

        parts = [f"## Brand Voice — {self.name}" if self.name else "## Brand Voice"]

        if self.tone_descriptors:
            parts.append(f"**Tone:** {', '.join(self.tone_descriptors)}")

        if self.voice_patterns:
            parts.append("\n### Voice Patterns")
            for vp in self.voice_patterns:
                parts.append(vp.to_prompt_line())

        if self.terminology:
            parts.append("\n### Terminology")
            for te in self.terminology:
                parts.append(te.to_prompt_line())

        if self.style_rules:
            parts.append("\n### Style Rules")
            for sr in self.style_rules:
                parts.append(sr.to_prompt_line())

        if self.do_list:
            parts.append("\n### Do")
            for d in self.do_list:
                parts.append(f"- {d}")

        if self.dont_list:
            parts.append("\n### Don't")
            for d in self.dont_list:
                parts.append(f"- {d}")

        return "\n".join(parts)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BrandDNA:
        voice_patterns = [VoicePattern(**vp) for vp in data.get("voice_patterns", [])]
        terminology = [TerminologyEntry(**te) for te in data.get("terminology", [])]
        style_rules = [StyleRule(**sr) for sr in data.get("style_rules", [])]
        return cls(
            name=data.get("name", ""),
            voice_patterns=voice_patterns,
            terminology=terminology,
            style_rules=style_rules,
            tone_descriptors=data.get("tone_descriptors", []),
            do_list=data.get("do_list", []),
            dont_list=data.get("dont_list", []),
            source_samples=data.get("source_samples", 0),
            created_at=data.get("created_at", 0.0),
            updated_at=data.get("updated_at", 0.0),
        )

    def merge(self, other: BrandDNA) -> None:
        """Merge another BrandDNA into this one, deduplicating."""
        existing_pattern_names = {vp.name for vp in self.voice_patterns}
        for vp in other.voice_patterns:
            if vp.name not in existing_pattern_names:
                self.voice_patterns.append(vp)
                existing_pattern_names.add(vp.name)

        existing_preferred = {te.preferred for te in self.terminology}
        for te in other.terminology:
            if te.preferred not in existing_preferred:
                self.terminology.append(te)
                existing_preferred.add(te.preferred)

        existing_rules = {sr.rule for sr in self.style_rules}
        for sr in other.style_rules:
            if sr.rule not in existing_rules:
                self.style_rules.append(sr)
                existing_rules.add(sr.rule)

        for td in other.tone_descriptors:
            if td not in self.tone_descriptors:
                self.tone_descriptors.append(td)

        for d in other.do_list:
            if d not in self.do_list:
                self.do_list.append(d)

        for d in other.dont_list:
            if d not in self.dont_list:
                self.dont_list.append(d)

        self.source_samples += other.source_samples
        self.updated_at = time.time()


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

BRAND_DNA_DIR = ".cd-agency"
BRAND_DNA_FILE = "brand_dna.json"

_MAX_VOICE_PATTERNS = 20
_MAX_TERMINOLOGY = 100
_MAX_STYLE_RULES = 50
_MAX_TONE_DESCRIPTORS = 10


def _brand_dna_path(project_dir: Path | None = None) -> Path:
    return (project_dir or Path(".")) / BRAND_DNA_DIR / BRAND_DNA_FILE


def load_brand_dna(project_dir: Path | None = None) -> BrandDNA:
    """Load brand DNA from the project directory."""
    path = _brand_dna_path(project_dir)
    if not path.exists():
        return BrandDNA()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return BrandDNA.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return BrandDNA()


def save_brand_dna(dna: BrandDNA, project_dir: Path | None = None) -> None:
    """Persist brand DNA to disk, enforcing storage limits."""
    dna.voice_patterns = dna.voice_patterns[:_MAX_VOICE_PATTERNS]
    dna.terminology = dna.terminology[:_MAX_TERMINOLOGY]
    dna.style_rules = dna.style_rules[:_MAX_STYLE_RULES]
    dna.tone_descriptors = dna.tone_descriptors[:_MAX_TONE_DESCRIPTORS]
    dna.updated_at = time.time()

    path = _brand_dna_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(dna.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def reset_brand_dna(project_dir: Path | None = None) -> bool:
    """Delete stored brand DNA. Returns True if file existed."""
    path = _brand_dna_path(project_dir)
    if path.exists():
        path.unlink()
        return True
    return False


# ---------------------------------------------------------------------------
# Processor — extracts brand DNA from content using LLM
# ---------------------------------------------------------------------------

_EXTRACTION_SYSTEM = """\
You are a brand voice analyst. Given content samples from a brand, extract:
1. Voice patterns (recurring tone, personality, communication style traits)
2. Terminology preferences (preferred terms vs avoided terms)
3. Style rules (punctuation, capitalization, formatting conventions)
4. Tone descriptors (3-5 adjectives describing the overall voice)
5. Do/Don't lists (concrete writing guidelines)

Return your analysis as JSON with this exact structure:
{
  "tone_descriptors": ["adjective1", "adjective2", ...],
  "voice_patterns": [
    {"name": "pattern-name", "description": "what it is", "examples": ["example1", "example2"], "confidence": 0.9}
  ],
  "terminology": [
    {"preferred": "sign in", "avoid": ["log in", "login"], "context": "authentication actions"}
  ],
  "style_rules": [
    {"rule": "Use sentence case for headings", "category": "capitalization", "examples": ["Save your changes"]}
  ],
  "do_list": ["Use active voice", "Address the user directly"],
  "dont_list": ["Don't use jargon", "Don't blame the user"]
}

Be specific and evidence-based. Only include patterns you can support with examples from the provided content.
Return JSON only, no other text."""


class BrandDNAProcessor:
    """Extracts brand DNA from content samples using LLM analysis."""

    def __init__(self, model_router: Any = None, model: str | None = None) -> None:
        self._router = model_router
        self._model = model

    def _get_router(self) -> Any:
        if self._router is None:
            from runtime.config import Config
            from runtime.model_providers import ModelRouter
            config = Config.from_env()
            self._router = ModelRouter.from_config(config)
            if self._model is None:
                self._model = config.model
        return self._router

    def ingest(self, content_samples: list[str], brand_name: str = "") -> BrandDNA:
        """Analyze content samples and extract brand DNA.

        Args:
            content_samples: List of representative content strings.
            brand_name: Optional brand name for the profile.

        Returns:
            BrandDNA with extracted patterns, terminology, and rules.
        """
        if not content_samples:
            return BrandDNA(name=brand_name)

        # Combine samples into a single analysis prompt
        samples_text = "\n\n---\n\n".join(
            f"**Sample {i + 1}:**\n{sample}"
            for i, sample in enumerate(content_samples[:20])  # Cap at 20 samples
        )

        user_message = (
            f"Analyze the following content samples"
            + (f" from the brand '{brand_name}'" if brand_name else "")
            + " and extract the brand voice DNA:\n\n"
            + samples_text
        )

        router = self._get_router()
        model = self._model or "claude-sonnet-4-20250514"
        provider, bare_model = router.resolve(model)

        response = provider.complete(
            model=bare_model,
            system=_EXTRACTION_SYSTEM,
            messages=[{"role": "user", "content": user_message}],
            max_tokens=4096,
            temperature=0.3,
        )

        dna = self._parse_response(response.content)
        dna.name = brand_name or dna.name
        dna.source_samples = len(content_samples)
        return dna

    def ingest_file(self, file_path: Path, brand_name: str = "") -> BrandDNA:
        """Ingest content from a file (text, markdown, or YAML)."""
        text = file_path.read_text(encoding="utf-8")

        if file_path.suffix in (".yaml", ".yml"):
            import yaml
            data = yaml.safe_load(text)
            samples = self._extract_samples_from_yaml(data)
        elif file_path.suffix == ".md":
            samples = self._split_markdown_sections(text)
        else:
            samples = self._split_text(text)

        return self.ingest(samples, brand_name=brand_name)

    def _parse_response(self, response_text: str) -> BrandDNA:
        """Parse LLM response into BrandDNA."""
        text = response_text.strip()

        # Handle markdown code blocks
        if "```" in text:
            match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
            if match:
                text = match.group(1).strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return BrandDNA()

        return BrandDNA(
            voice_patterns=[
                VoicePattern(**vp) for vp in data.get("voice_patterns", [])
            ],
            terminology=[
                TerminologyEntry(**te) for te in data.get("terminology", [])
            ],
            style_rules=[
                StyleRule(**sr) for sr in data.get("style_rules", [])
            ],
            tone_descriptors=data.get("tone_descriptors", []),
            do_list=data.get("do_list", []),
            dont_list=data.get("dont_list", []),
        )

    @staticmethod
    def _extract_samples_from_yaml(data: Any) -> list[str]:
        """Pull string values from a YAML structure as content samples."""
        samples: list[str] = []

        def _walk(obj: Any) -> None:
            if isinstance(obj, str) and len(obj) > 20:
                samples.append(obj)
            elif isinstance(obj, list):
                for item in obj:
                    _walk(item)
            elif isinstance(obj, dict):
                for v in obj.values():
                    _walk(v)

        _walk(data)
        return samples[:20]

    @staticmethod
    def _split_markdown_sections(text: str) -> list[str]:
        """Split markdown into sections by headings."""
        sections = re.split(r"\n(?=#{1,3}\s)", text)
        return [s.strip() for s in sections if len(s.strip()) > 30][:20]

    @staticmethod
    def _split_text(text: str) -> list[str]:
        """Split plain text into paragraph-sized chunks."""
        paragraphs = re.split(r"\n\n+", text)
        return [p.strip() for p in paragraphs if len(p.strip()) > 20][:20]

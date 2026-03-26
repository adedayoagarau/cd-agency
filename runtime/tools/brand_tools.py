"""Brand DNA tools — let agents extract and query brand voice patterns."""

from __future__ import annotations

from typing import Any

from runtime.tools.base import Tool, ToolResult


class ExtractBrandPatterns(Tool):
    """Extract brand voice patterns from content samples."""

    name = "extract_brand_patterns"
    description = (
        "Analyze content samples to extract brand voice patterns, terminology "
        "preferences, and style rules. Use when ingesting brand content to learn "
        "a brand's voice DNA."
    )
    parameters = {
        "content": {"type": "string", "description": "Content sample to analyze for brand patterns"},
        "brand_name": {
            "type": "string",
            "description": "Brand name for the voice profile",
            "optional": True,
        },
    }

    def execute(self, **kwargs: Any) -> ToolResult:
        content = kwargs.get("content", "")
        brand_name = kwargs.get("brand_name", "")

        if not content or len(content.strip()) < 20:
            return ToolResult(
                success=False,
                error="Content sample is too short. Provide at least 20 characters.",
            )

        try:
            from runtime.brand_dna import BrandDNAProcessor, load_brand_dna, save_brand_dna

            processor = BrandDNAProcessor()
            new_dna = processor.ingest([content], brand_name=brand_name)

            if new_dna.is_empty():
                return ToolResult(
                    success=False,
                    error="Could not extract any brand patterns from the content.",
                )

            # Merge with existing brand DNA
            existing = load_brand_dna()
            existing.merge(new_dna)
            if brand_name:
                existing.name = brand_name
            save_brand_dna(existing)

            return ToolResult(
                success=True,
                data={
                    "voice_patterns": len(new_dna.voice_patterns),
                    "terminology_entries": len(new_dna.terminology),
                    "style_rules": len(new_dna.style_rules),
                    "tone_descriptors": new_dna.tone_descriptors,
                    "total_patterns": (
                        len(new_dna.voice_patterns)
                        + len(new_dna.terminology)
                        + len(new_dna.style_rules)
                    ),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Brand extraction failed: {e}")


class QueryBrandDNA(Tool):
    """Query the stored brand DNA for voice guidance."""

    name = "query_brand_dna"
    description = (
        "Retrieve the stored brand voice DNA — voice patterns, terminology "
        "preferences, and style rules. Use when you need to write content "
        "that matches the brand voice."
    )
    parameters = {}

    def execute(self, **kwargs: Any) -> ToolResult:
        try:
            from runtime.brand_dna import load_brand_dna

            dna = load_brand_dna()
            if dna.is_empty():
                return ToolResult(
                    success=True,
                    data={"has_brand_dna": False, "message": "No brand DNA stored yet."},
                )

            return ToolResult(
                success=True,
                data={
                    "has_brand_dna": True,
                    "name": dna.name,
                    "tone_descriptors": dna.tone_descriptors,
                    "voice_patterns": len(dna.voice_patterns),
                    "terminology_entries": len(dna.terminology),
                    "style_rules": len(dna.style_rules),
                    "context_block": dna.build_context_block(),
                },
            )
        except Exception as e:
            return ToolResult(success=False, error=f"Brand DNA query failed: {e}")

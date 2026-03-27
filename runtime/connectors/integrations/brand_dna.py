"""Brand DNA integration for connector content."""
from __future__ import annotations

import logging
from typing import Any

from runtime.connectors.base import ContentItem

_logger = logging.getLogger(__name__)


class ConnectorBrandAnalyzer:
    """Extracts brand signals from connector content for Brand DNA enrichment."""

    def analyze_content(self, item: ContentItem) -> dict[str, Any]:
        """Analyze a content item for brand signals."""
        content = item.content or ""
        return {
            "tone_indicators": self._detect_tone(content),
            "terminology": self._extract_terms(content),
            "content_structure": {
                "has_title": bool(item.title),
                "content_length": len(content),
                "tag_count": len(item.tags),
                "content_type": item.content_type.value if item.content_type else None,
            },
            "source_platform": item.connector_id or "",
        }

    def analyze_batch(self, items: list[ContentItem]) -> dict[str, Any]:
        """Analyze multiple items and aggregate signals."""
        if not items:
            return {"items_analyzed": 0, "signals": []}
        signals = [self.analyze_content(i) for i in items]
        tones: dict[str, int] = {}
        for s in signals:
            for t in s["tone_indicators"]:
                tones[t] = tones.get(t, 0) + 1
        return {
            "items_analyzed": len(items),
            "dominant_tones": sorted(tones, key=tones.get, reverse=True)[:5],
            "avg_content_length": sum(s["content_structure"]["content_length"] for s in signals) / len(signals),
            "signals": signals,
        }

    def _detect_tone(self, content: str) -> list[str]:
        indicators = []
        lower = content.lower()
        tone_words = {
            "enthusiastic": ["exciting", "amazing", "fantastic", "incredible", "awesome"],
            "professional": ["professional", "enterprise", "business", "corporate", "solution"],
            "friendly": ["friendly", "welcome", "hello", "hey", "glad"],
            "urgent": ["immediately", "urgent", "critical", "now", "asap"],
            "casual": ["cool", "awesome", "btw", "gonna", "wanna"],
        }
        for tone, words in tone_words.items():
            if any(w in lower for w in words):
                indicators.append(tone)
        return indicators

    def _extract_terms(self, content: str) -> list[str]:
        words = content.split()
        return list({w.lower().strip(".,!?;:\"'()") for w in words if len(w) > 6})[:20]

"""Tests for connector integrations (brand DNA, memory)."""

from __future__ import annotations

import pytest

from runtime.connectors.base import ContentItem, ContentType
from runtime.connectors.integrations.brand_dna import ConnectorBrandAnalyzer
from runtime.connectors.integrations.memory import ConnectorMemoryBridge


# ---------------------------------------------------------------------------
# ConnectorBrandAnalyzer
# ---------------------------------------------------------------------------


class TestConnectorBrandAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return ConnectorBrandAnalyzer()

    def test_analyze_empty_content(self, analyzer):
        item = ContentItem(id="1", content="", connector_id="test")
        result = analyzer.analyze_content(item)
        assert result["tone_indicators"] == []
        assert result["content_structure"]["content_length"] == 0
        assert result["source_platform"] == "test"

    def test_analyze_professional_content(self, analyzer):
        item = ContentItem(
            id="1",
            title="Enterprise Solution",
            content="Our professional business solution provides enterprise-grade functionality.",
            content_type=ContentType.ARTICLE,
            tags=["business", "enterprise"],
            connector_id="contentful",
        )
        result = analyzer.analyze_content(item)
        assert "professional" in result["tone_indicators"]
        assert result["content_structure"]["has_title"] is True
        assert result["content_structure"]["tag_count"] == 2
        assert result["content_structure"]["content_type"] == "article"

    def test_analyze_casual_content(self, analyzer):
        item = ContentItem(
            id="2",
            content="Hey, that's awesome! Gonna check this out btw.",
            connector_id="notion",
        )
        result = analyzer.analyze_content(item)
        assert "casual" in result["tone_indicators"]

    def test_analyze_batch_empty(self, analyzer):
        result = analyzer.analyze_batch([])
        assert result["items_analyzed"] == 0
        assert result["signals"] == []

    def test_analyze_batch(self, analyzer):
        items = [
            ContentItem(id="1", content="Professional business enterprise solution", connector_id="a"),
            ContentItem(id="2", content="Hey awesome cool stuff gonna love it", connector_id="a"),
            ContentItem(id="3", content="Professional corporate business guide", connector_id="a"),
        ]
        result = analyzer.analyze_batch(items)
        assert result["items_analyzed"] == 3
        assert "professional" in result["dominant_tones"]
        assert result["avg_content_length"] > 0
        assert len(result["signals"]) == 3

    def test_term_extraction(self, analyzer):
        item = ContentItem(
            id="1",
            content="The microservices architecture provides excellent scalability.",
            connector_id="x",
        )
        result = analyzer.analyze_content(item)
        terms = result["terminology"]
        assert isinstance(terms, list)
        # Should extract words > 6 chars
        assert any("microservices" in t for t in terms) or any("architecture" in t for t in terms)


# ---------------------------------------------------------------------------
# ConnectorMemoryBridge
# ---------------------------------------------------------------------------


class TestConnectorMemoryBridge:
    def test_store_without_memory(self):
        bridge = ConnectorMemoryBridge(memory=None)
        item = ContentItem(id="1", title="Test", connector_id="test")
        # Should not crash when memory is unavailable
        result = bridge.store_content_signals(item, {"tone": ["friendly"]})
        # May return True or False depending on ProjectMemory availability
        assert isinstance(result, bool)

    def test_get_context_without_memory(self):
        bridge = ConnectorMemoryBridge(memory=None)
        result = bridge.get_connector_context("test")
        assert result == "" or isinstance(result, str)

    def test_store_with_mock_memory(self):
        from unittest.mock import MagicMock

        mock_memory = MagicMock()
        mock_memory.remember = MagicMock()
        bridge = ConnectorMemoryBridge(memory=mock_memory)

        item = ContentItem(
            id="item-1",
            title="Test Article",
            content_type=ContentType.ARTICLE,
            connector_id="contentful",
        )
        result = bridge.store_content_signals(item, {"tone": ["professional"]})
        assert result is True
        mock_memory.remember.assert_called_once()

    def test_get_context_with_mock_memory(self):
        from unittest.mock import MagicMock

        mock_memory = MagicMock()
        mock_memory.recall.return_value = "Some recalled context"
        bridge = ConnectorMemoryBridge(memory=mock_memory)

        ctx = bridge.get_connector_context("contentful")
        assert "contentful" in ctx
        assert "Some recalled context" in ctx

"""Tests for connector providers."""

from __future__ import annotations

from typing import Any

import pytest

from runtime.connectors.base import (
    ConnectorConfig,
    ConnectorStatus,
    ContentItem,
    ContentType,
    HealthCheck,
)


# ---------------------------------------------------------------------------
# Contentful
# ---------------------------------------------------------------------------


class TestContentfulConnector:
    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            name="test-contentful",
            type="contentful",
            credentials={
                "space_id": "test_space",
                "access_token": "test_token",
                "environment": "master",
            },
            settings={"locale": "en-US", "include_drafts": False},
        )

    def test_init(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        assert conn.CONNECTOR_TYPE == "contentful"
        assert conn.space_id == "test_space"
        assert conn.access_token == "test_token"
        assert conn.locale == "en-US"
        assert "cdn.contentful.com" in conn._api_base

    def test_init_preview(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        config.settings["include_drafts"] = True
        conn = ContentfulConnector(config)
        assert "preview.contentful.com" in conn._api_base

    def test_headers(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        headers = conn._get_default_headers()
        assert headers["Authorization"] == "Bearer test_token"

    def test_supported_types(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        types = conn.get_supported_content_types()
        assert ContentType.ARTICLE in types
        assert ContentType.PAGE in types

    def test_create_raises(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        with pytest.raises(NotImplementedError):
            conn.create_content(ContentItem(id="x"))

    def test_update_raises(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        with pytest.raises(NotImplementedError):
            conn.update_content("x", ContentItem(id="x"))

    def test_delete_raises(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        with pytest.raises(NotImplementedError):
            conn.delete_content("x")

    def test_parse_entry(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        entry = {
            "sys": {
                "id": "entry-1",
                "createdAt": "2024-01-01T00:00:00Z",
                "updatedAt": "2024-06-01T00:00:00Z",
                "contentType": {"sys": {"id": "blogPost"}},
            },
            "fields": {
                "title": "Test Post",
                "body": "Hello world",
            },
        }
        item = conn._parse_entry(entry)
        assert item.id == "entry-1"
        assert item.title == "Test Post"
        assert item.content == "Hello world"
        assert item.content_type == ContentType.ARTICLE
        assert item.created_at is not None
        assert item.updated_at is not None

    def test_parse_rich_text(self, config):
        from runtime.connectors.providers.contentful import ContentfulConnector

        conn = ContentfulConnector(config)
        rich_text = {
            "nodeType": "document",
            "content": [
                {
                    "nodeType": "paragraph",
                    "content": [
                        {"nodeType": "text", "value": "Hello "},
                        {"nodeType": "text", "value": "world"},
                    ],
                }
            ],
        }
        result = conn._extract_rich_text(rich_text)
        assert "Hello" in result
        assert "world" in result


# ---------------------------------------------------------------------------
# Figma
# ---------------------------------------------------------------------------


class TestFigmaConnector:
    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            name="test-figma",
            type="figma",
            credentials={"personal_access_token": "figma-token"},
            settings={"team_id": "team-123"},
        )

    def test_init(self, config):
        from runtime.connectors.providers.figma import FigmaConnector

        conn = FigmaConnector(config)
        assert conn.CONNECTOR_TYPE == "figma"
        assert conn.team_id == "team-123"

    def test_headers(self, config):
        from runtime.connectors.providers.figma import FigmaConnector

        conn = FigmaConnector(config)
        headers = conn._get_default_headers()
        assert "X-Figma-Token" in headers

    def test_supported_types(self, config):
        from runtime.connectors.providers.figma import FigmaConnector

        conn = FigmaConnector(config)
        types = conn.get_supported_content_types()
        assert ContentType.DESIGN in types
        assert ContentType.COMPONENT in types

    def test_create_raises(self, config):
        from runtime.connectors.providers.figma import FigmaConnector

        conn = FigmaConnector(config)
        with pytest.raises(NotImplementedError):
            conn.create_content(ContentItem(id="x"))

    def test_delete_raises(self, config):
        from runtime.connectors.providers.figma import FigmaConnector

        conn = FigmaConnector(config)
        with pytest.raises(NotImplementedError):
            conn.delete_content("x")


# ---------------------------------------------------------------------------
# Notion
# ---------------------------------------------------------------------------


class TestNotionConnector:
    @pytest.fixture
    def config(self):
        return ConnectorConfig(
            name="test-notion",
            type="notion",
            credentials={"api_key": "notion-key"},
            settings={"database_id": "db-123", "version": "2022-06-28"},
        )

    def test_init(self, config):
        from runtime.connectors.providers.notion import NotionConnector

        conn = NotionConnector(config)
        assert conn.CONNECTOR_TYPE == "notion"
        assert conn.api_token == "notion-key"
        assert conn.database_id == "db-123"

    def test_headers(self, config):
        from runtime.connectors.providers.notion import NotionConnector

        conn = NotionConnector(config)
        headers = conn._get_default_headers()
        assert "notion-key" in headers.get("Authorization", "")
        assert headers.get("Notion-Version") == "2022-06-28"

    def test_supported_types(self, config):
        from runtime.connectors.providers.notion import NotionConnector

        conn = NotionConnector(config)
        types = conn.get_supported_content_types()
        assert ContentType.PAGE in types
        assert ContentType.DATABASE in types
        assert ContentType.DOCUMENT in types

    def test_parse_rich_text_array(self, config):
        from runtime.connectors.providers.notion import NotionConnector

        conn = NotionConnector(config)
        rt = [
            {"plain_text": "Hello "},
            {"plain_text": "world"},
        ]
        assert conn._extract_title_from_rich_text(rt) == "Hello world"

    def test_parse_rich_text_empty(self, config):
        from runtime.connectors.providers.notion import NotionConnector

        conn = NotionConnector(config)
        assert conn._extract_title_from_rich_text([]) == ""


# ---------------------------------------------------------------------------
# Stub connectors
# ---------------------------------------------------------------------------


class TestStubConnectors:
    @pytest.fixture
    def stub_config(self):
        return ConnectorConfig(name="stub", type="stub")

    def test_sanity_stub(self, stub_config):
        from runtime.connectors.providers.sanity import SanityConnector

        conn = SanityConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "sanity"
        assert conn.authenticate() is False
        h = conn.health_check()
        assert h.status == ConnectorStatus.UNHEALTHY
        assert conn.list_content() == []
        assert conn.get_content("x") is None
        with pytest.raises(NotImplementedError):
            conn.create_content(ContentItem(id="x"))

    def test_strapi_stub(self, stub_config):
        from runtime.connectors.providers.strapi import StrapiConnector

        conn = StrapiConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "strapi"
        assert conn.authenticate() is False

    def test_wordpress_stub(self, stub_config):
        from runtime.connectors.providers.wordpress import WordPressConnector

        conn = WordPressConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "wordpress"
        assert conn.authenticate() is False

    def test_storyblok_stub(self, stub_config):
        from runtime.connectors.providers.storyblok import StoryblokConnector

        conn = StoryblokConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "storyblok"
        assert conn.authenticate() is False

    def test_airtable_stub(self, stub_config):
        from runtime.connectors.providers.airtable import AirtableConnector

        conn = AirtableConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "airtable"
        assert conn.authenticate() is False

    def test_google_docs_stub(self, stub_config):
        from runtime.connectors.providers.google_docs import GoogleDocsConnector

        conn = GoogleDocsConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "google_docs"
        assert conn.authenticate() is False

    def test_markdown_stub(self, stub_config):
        from runtime.connectors.providers.markdown_connector import MarkdownConnector

        conn = MarkdownConnector(stub_config)
        assert conn.CONNECTOR_TYPE == "markdown"

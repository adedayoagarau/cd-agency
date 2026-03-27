"""Tests for the FastAPI REST API endpoints."""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── Health ───────────────────────────────────────────────────────────────────


class TestHealth:
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


# ── Agents ───────────────────────────────────────────────────────────────────


class TestAgentEndpoints:
    def test_list_agents(self):
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 16
        slugs = [a["slug"] for a in data]
        assert "error-message-architect" in slugs
        assert "information-architect" in slugs

    def test_get_agent_detail(self):
        response = client.get("/api/v1/agents/error-message-architect")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "error-message-architect"
        assert data["name"] == "Error Message Architect"
        assert len(data["inputs"]) > 0
        assert len(data["outputs"]) > 0

    def test_get_agent_not_found(self):
        response = client.get("/api/v1/agents/nonexistent-agent")
        assert response.status_code == 404

    def test_search_agents(self):
        response = client.get("/api/v1/agents/search?q=error")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("error" in a["slug"] for a in data)


# ── Scoring ──────────────────────────────────────────────────────────────────


class TestScoringEndpoints:
    def test_score_readability(self):
        response = client.post(
            "/api/v1/score/readability",
            json={"text": "This is a simple test sentence for readability scoring."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "flesch_reading_ease" in data
        assert "flesch_kincaid_grade" in data
        assert data["word_count"] > 0

    def test_score_lint(self):
        response = client.post(
            "/api/v1/score/lint",
            json={"text": "Let's leverage our synergy to move the needle."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "issues" in data
        assert data["failed_count"] > 0  # Should flag jargon

    def test_score_a11y(self):
        response = client.post(
            "/api/v1/score/a11y",
            json={"text": "Click here to learn more about our services and products."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "passed" in data
        assert "issues" in data

    def test_score_all(self):
        response = client.post(
            "/api/v1/score/all",
            json={"text": "Save your changes before leaving this page."},
        )
        assert response.status_code == 200
        data = response.json()
        assert "readability" in data
        assert "lint" in data
        assert "a11y" in data

    def test_score_empty_text_rejected(self):
        response = client.post("/api/v1/score/readability", json={"text": ""})
        assert response.status_code == 422


# ── Validation ───────────────────────────────────────────────────────────────


class TestValidationEndpoints:
    def test_validate_button_passes(self):
        response = client.post(
            "/api/v1/validate",
            json={"text": "Save", "element_type": "button"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["passed"] is True
        assert data["error_count"] == 0

    def test_validate_button_too_long(self):
        response = client.post(
            "/api/v1/validate",
            json={"text": "Complete your purchase and save your items to checkout now", "element_type": "button"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["passed"] is False
        assert data["error_count"] >= 1
        assert any(v["rule"] == "character_limit" for v in data["violations"])

    def test_validate_with_platform(self):
        response = client.post(
            "/api/v1/validate",
            json={"text": "save changes", "element_type": "button", "platform": "ios"},
        )
        assert response.status_code == 200
        data = response.json()
        # iOS expects Title Case for buttons
        assert any(v["rule"] == "platform_case" for v in data["violations"])

    def test_validate_with_localization(self):
        response = client.post(
            "/api/v1/validate",
            json={
                "text": "Complete your purchase now",
                "element_type": "button",
                "target_language": "de",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # German expands 35%, so 25-char text should warn
        assert any(v["rule"] == "localization_expansion" for v in data["violations"])

    def test_validate_a11y_click_here(self):
        response = client.post(
            "/api/v1/validate",
            json={"text": "Click here for details", "element_type": "button"},
        )
        assert response.status_code == 200
        data = response.json()
        assert any(v["rule"] == "a11y_link_text" for v in data["violations"])

    def test_list_element_types(self):
        response = client.get("/api/v1/validate/element-types")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 15
        types = [et["type"] for et in data]
        assert "button" in types
        assert "toast" in types
        assert "push_body" in types

    def test_validate_empty_text_rejected(self):
        response = client.post(
            "/api/v1/validate",
            json={"text": "", "element_type": "button"},
        )
        assert response.status_code == 422


# ── Content History ──────────────────────────────────────────────────────────


class TestHistoryEndpoints:
    def test_list_history_empty(self):
        """History list should return an empty list when no versions exist."""
        with patch("api.routers.history.ContentHistory") as mock_cls:
            mock_hist = mock_cls.load.return_value
            mock_hist.list_recent.return_value = []
            response = client.get("/api/v1/history")
            assert response.status_code == 200
            assert response.json() == []

    def test_get_version_not_found(self):
        with patch("api.routers.history.ContentHistory") as mock_cls:
            mock_hist = mock_cls.load.return_value
            mock_hist.get.return_value = None
            response = client.get("/api/v1/history/nonexistent123")
            assert response.status_code == 404

    def test_diff_not_found(self):
        with patch("api.routers.history.ContentHistory") as mock_cls:
            mock_hist = mock_cls.load.return_value
            mock_hist.diff.return_value = None
            response = client.get("/api/v1/history/nonexistent123/diff")
            assert response.status_code == 404

    def test_stats_empty(self):
        with patch("api.routers.history.ContentHistory") as mock_cls:
            mock_hist = mock_cls.load.return_value
            mock_hist.summary.return_value = {"count": 0, "agents_used": [], "latest": None}
            response = client.get("/api/v1/history/stats")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0

    def test_search_history(self):
        with patch("api.routers.history.ContentHistory") as mock_cls:
            mock_hist = mock_cls.load.return_value
            mock_hist.search.return_value = []
            response = client.get("/api/v1/history/search?q=payment")
            assert response.status_code == 200
            assert response.json() == []


# ── Presets ──────────────────────────────────────────────────────────────────


class TestPresetEndpoints:
    def test_list_presets(self):
        response = client.get("/api/v1/presets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4
        names = [p["name"] for p in data]
        assert "Material Design" in names or "material-design" in [p["filename"].replace(".yaml", "") for p in data]

    def test_get_preset_not_found(self):
        response = client.get("/api/v1/presets/nonexistent-preset")
        assert response.status_code == 404


# ── Workflows ───────────────────────────────────────────────────────────────


class TestWorkflowEndpoints:
    def test_list_workflows(self):
        response = client.get("/api/v1/workflows")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 5
        slugs = [w["slug"] for w in data]
        assert "content-audit" in slugs

    def test_get_workflow_detail(self):
        response = client.get("/api/v1/workflows/content-audit")
        assert response.status_code == 200
        data = response.json()
        assert data["slug"] == "content-audit"
        assert len(data["steps"]) > 0

    def test_get_workflow_not_found(self):
        response = client.get("/api/v1/workflows/nonexistent-workflow")
        assert response.status_code == 404


# ── Export ──────────────────────────────────────────────────────────────────


class TestExportEndpoints:
    def test_export_json(self):
        response = client.post(
            "/api/v1/export",
            json={
                "entries": [
                    {"source": "Error 500", "target": "Something went wrong", "context": "server error"}
                ],
                "format": "json",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.text)
        assert "entries" in data
        assert len(data["entries"]) == 1

    def test_export_csv(self):
        response = client.post(
            "/api/v1/export",
            json={
                "entries": [
                    {"source": "Save", "target": "Save changes"}
                ],
                "format": "csv",
            },
        )
        assert response.status_code == 200
        assert "Source" in response.text
        assert "Save" in response.text

    def test_export_markdown(self):
        response = client.post(
            "/api/v1/export",
            json={
                "entries": [
                    {"source": "Cancel", "target": "Discard changes"}
                ],
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        assert "Cancel" in response.text

    def test_export_xliff(self):
        response = client.post(
            "/api/v1/export",
            json={
                "entries": [
                    {"source": "OK", "target": "Got it"}
                ],
                "format": "xliff",
            },
        )
        assert response.status_code == 200
        assert "<xliff" in response.text

    def test_export_invalid_format(self):
        response = client.post(
            "/api/v1/export",
            json={
                "entries": [{"source": "a", "target": "b"}],
                "format": "pdf",
            },
        )
        assert response.status_code == 422

    def test_export_formats_list(self):
        response = client.get("/api/v1/export/formats")
        assert response.status_code == 200
        data = response.json()
        ids = [f["id"] for f in data]
        assert "json" in ids
        assert "csv" in ids
        assert "xliff" in ids


# ── Conversation ────────────────────────────────────────────────────────────


class TestConversationEndpoints:
    def test_chat_agent_not_found(self):
        response = client.post(
            "/api/v1/agents/nonexistent/chat",
            json={
                "messages": [{"role": "user", "content": "hello"}]
            },
            headers={"X-Anthropic-Key": "test-key"},
        )
        assert response.status_code == 404

    def test_chat_empty_messages_rejected(self):
        response = client.post(
            "/api/v1/agents/error-message-architect/chat",
            json={"messages": []},
            headers={"X-Anthropic-Key": "test-key"},
        )
        assert response.status_code == 422


# ── Batch ───────────────────────────────────────────────────────────────────


class TestBatchEndpoints:
    def test_batch_agent_not_found(self):
        response = client.post(
            "/api/v1/agents/nonexistent/batch",
            json={
                "items": [{"input": {"error_message": "Error 500"}}]
            },
            headers={"X-Anthropic-Key": "test-key"},
        )
        assert response.status_code == 404

    def test_batch_empty_items_rejected(self):
        response = client.post(
            "/api/v1/agents/error-message-architect/batch",
            json={"items": []},
            headers={"X-Anthropic-Key": "test-key"},
        )
        assert response.status_code == 422


# ── BYOK ────────────────────────────────────────────────────────────────────


class TestBYOK:
    def test_run_agent_without_key_returns_401(self):
        """Agent run should fail without any API key when server has none."""
        with patch.dict("os.environ", {}, clear=False):
            # Remove server key if present
            import os
            old_key = os.environ.pop("ANTHROPIC_API_KEY", None)
            try:
                response = client.post(
                    "/api/v1/agents/error-message-architect/run",
                    json={"input": {"error_message": "Error 500"}},
                )
                assert response.status_code == 401
            finally:
                if old_key:
                    os.environ["ANTHROPIC_API_KEY"] = old_key

    def test_scoring_works_without_api_key(self):
        """Scoring endpoints should work without any Anthropic key."""
        response = client.post(
            "/api/v1/score/readability",
            json={"text": "This is a test sentence."},
        )
        assert response.status_code == 200

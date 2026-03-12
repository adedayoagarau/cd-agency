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
        assert response.json() == {"status": "ok"}


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

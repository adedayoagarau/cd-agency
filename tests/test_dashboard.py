"""Tests for the observability dashboard."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from runtime.dashboard import (
    AgentMetrics,
    Dashboard,
    DashboardData,
    QualityTrend,
    SystemHealth,
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class TestDataStructures:
    def test_system_health_defaults(self):
        h = SystemHealth()
        assert h.total_agent_runs == 0
        assert h.avg_quality_score == 0.0

    def test_agent_metrics_defaults(self):
        m = AgentMetrics(slug="test-agent")
        assert m.total_runs == 0
        assert m.pass_rate == 0.0

    def test_quality_trend(self):
        t = QualityTrend(
            timestamp=1000, composite_score=85.0,
            agent_slug="test", passed=True,
        )
        assert t.composite_score == 85.0

    def test_dashboard_data_timestamp(self):
        d = DashboardData()
        assert d.generated_at > 0


# ---------------------------------------------------------------------------
# Dashboard collection
# ---------------------------------------------------------------------------

class TestDashboard:
    def test_collect_empty(self, tmp_path):
        dashboard = Dashboard(project_dir=tmp_path)
        data = dashboard.collect()

        assert isinstance(data, DashboardData)
        # Analytics may pick up global data; just verify structure
        assert isinstance(data.system_health, SystemHealth)

    def test_render_empty(self, tmp_path):
        dashboard = Dashboard(project_dir=tmp_path)
        output = dashboard.render()

        assert "CD AGENCY" in output
        assert "SYSTEM HEALTH" in output
        assert "QUALITY" in output

    def test_collect_with_evaluation_history(self, tmp_path):
        """Dashboard should collect from evaluation history if available."""
        import json
        import time

        # Create evaluation history
        history_dir = tmp_path / ".cd-agency"
        history_dir.mkdir(parents=True)
        entries = [
            {
                "timestamp": time.time(),
                "agent_slug": "test-agent",
                "scores": {"readability": {"flesch_reading_ease": 75}},
                "composite_score": 80.0,
                "passed": True,
                "iteration_count": 1,
            },
            {
                "timestamp": time.time(),
                "agent_slug": "test-agent",
                "scores": {"readability": {"flesch_reading_ease": 60}},
                "composite_score": 65.0,
                "passed": False,
                "iteration_count": 2,
            },
        ]
        (history_dir / "evaluation_history.json").write_text(
            json.dumps(entries), encoding="utf-8"
        )

        dashboard = Dashboard(project_dir=tmp_path)
        data = dashboard.collect()

        assert data.system_health.avg_quality_score > 0
        assert data.system_health.overall_pass_rate == 0.5

    def test_collect_with_feedback(self, tmp_path):
        """Dashboard should collect from feedback store."""
        import json

        feedback_dir = tmp_path / ".cd-agency" / "feedback"
        feedback_dir.mkdir(parents=True)

        edits = [
            {
                "id": "e1",
                "timestamp": 1000.0,
                "agent_slug": "test-agent",
                "agent_name": "Test Agent",
                "original": "before",
                "edited": "after",
                "similarity": 0.7,
                "edit_type": "minor_tweak",
                "metadata": {},
            }
        ]
        (feedback_dir / "edits.json").write_text(
            json.dumps(edits), encoding="utf-8"
        )

        patterns = [
            {
                "id": "p1",
                "pattern_type": "word_replacement",
                "description": "test",
                "original_pattern": "a",
                "corrected_pattern": "b",
                "occurrences": 3,
                "agent_slugs": ["test-agent"],
                "confidence": 0.5,
                "first_seen": 1000.0,
                "last_seen": 1000.0,
                "metadata": {},
            }
        ]
        (feedback_dir / "patterns.json").write_text(
            json.dumps(patterns), encoding="utf-8"
        )

        dashboard = Dashboard(project_dir=tmp_path)
        data = dashboard.collect()

        assert data.system_health.total_feedback_edits == 1
        assert data.system_health.learned_patterns == 1

    def test_collect_with_governance(self, tmp_path):
        """Dashboard should collect from governance system."""
        import json

        gov_dir = tmp_path / ".cd-agency"
        gov_dir.mkdir(parents=True)

        audit = [
            {
                "id": "a1",
                "timestamp": 1000.0,
                "action": "change_proposed",
                "change_type": "terminology",
                "actor": "user",
                "description": "test",
                "before_value": "",
                "after_value": "",
                "metadata": {},
            }
        ]
        (gov_dir / "audit_log.json").write_text(
            json.dumps(audit), encoding="utf-8"
        )

        changes = [
            {
                "id": "c1",
                "timestamp": 1000.0,
                "change_type": "terminology",
                "key": "login",
                "before_value": "log in",
                "after_value": "sign in",
                "reason": "",
                "source_agent": "",
                "approval_status": "pending",
                "approved_by": "",
                "approval_timestamp": 0,
                "metadata": {},
            }
        ]
        (gov_dir / "change_records.json").write_text(
            json.dumps(changes), encoding="utf-8"
        )

        dashboard = Dashboard(project_dir=tmp_path)
        data = dashboard.collect()

        assert data.system_health.pending_approvals == 1
        assert data.system_health.audit_entries == 1

    def test_render_with_data(self, tmp_path):
        """Render should include all sections."""
        import json
        import time

        # Set up evaluation history
        history_dir = tmp_path / ".cd-agency"
        history_dir.mkdir(parents=True)
        entries = [
            {
                "timestamp": time.time(),
                "agent_slug": "test-agent",
                "scores": {},
                "composite_score": 80.0,
                "passed": True,
                "iteration_count": 1,
            }
        ]
        (history_dir / "evaluation_history.json").write_text(
            json.dumps(entries), encoding="utf-8"
        )

        dashboard = Dashboard(project_dir=tmp_path)
        output = dashboard.render()

        assert "SYSTEM HEALTH" in output
        assert "QUALITY" in output
        assert "FEEDBACK & GOVERNANCE" in output

    def test_build_agent_metrics(self, tmp_path):
        dashboard = Dashboard(project_dir=tmp_path)

        analytics = {
            "agent_data": {
                "Error Agent": {"runs": 10, "tokens": 5000, "avg_latency": 200},
            },
        }
        evaluation = {
            "agent_eval": {
                "error-agent": {"scores": [80, 85, 90], "passed": 3, "total": 3},
            },
        }
        feedback = {
            "agent_stats": {
                "error-agent": {"edits": 2, "similarities": [0.8, 0.9]},
            },
        }

        metrics = dashboard._build_agent_metrics(analytics, evaluation, feedback)
        assert len(metrics) >= 1

    def test_build_recent_activity(self, tmp_path):
        dashboard = Dashboard(project_dir=tmp_path)

        versioning = {
            "recent_versions": [
                {"timestamp": 1000, "agent": "Test", "preview": "content..."},
            ],
        }
        governance = {
            "recent_changes": [
                {"timestamp": 1001, "type": "terminology", "key": "login", "status": "pending"},
            ],
        }
        feedback = {
            "recent_edits": [
                {"timestamp": 1002, "agent": "test", "edit_type": "minor_tweak", "similarity": 0.9},
            ],
        }

        activity = dashboard._build_recent_activity(versioning, governance, feedback)
        assert len(activity) == 3
        # Should be sorted by timestamp (most recent first)
        assert activity[0]["timestamp"] >= activity[-1]["timestamp"]

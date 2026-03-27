"""Observability dashboard — aggregates metrics across all cd-agency systems.

Pulls data from analytics, evaluation history, content versioning,
feedback loop, and governance to provide a unified view of system health,
quality trends, and usage patterns.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentMetrics:
    """Per-agent quality and usage metrics."""

    slug: str
    name: str = ""
    total_runs: int = 0
    total_tokens: int = 0
    avg_latency_ms: float = 0.0
    avg_composite_score: float = 0.0
    pass_rate: float = 0.0  # 0-1
    total_edits: int = 0
    avg_edit_similarity: float = 0.0  # 0-1, higher = fewer human changes
    recent_scores: list[float] = field(default_factory=list)


@dataclass
class QualityTrend:
    """Quality trend data point."""

    timestamp: float = 0.0
    composite_score: float = 0.0
    agent_slug: str = ""
    passed: bool = True


@dataclass
class SystemHealth:
    """Overall system health metrics."""

    total_agent_runs: int = 0
    total_workflow_runs: int = 0
    total_tokens_used: int = 0
    total_content_versions: int = 0
    active_agents: int = 0
    avg_quality_score: float = 0.0
    overall_pass_rate: float = 0.0
    pending_approvals: int = 0
    total_feedback_edits: int = 0
    learned_patterns: int = 0
    audit_entries: int = 0
    uptime_days: float = 0.0


@dataclass
class DashboardData:
    """Complete dashboard data aggregation."""

    generated_at: float = 0.0
    system_health: SystemHealth = field(default_factory=SystemHealth)
    agent_metrics: list[AgentMetrics] = field(default_factory=list)
    quality_trends: list[QualityTrend] = field(default_factory=list)
    top_agents: list[dict[str, Any]] = field(default_factory=list)
    recent_activity: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = time.time()


class Dashboard:
    """Aggregates metrics from all cd-agency data sources."""

    def __init__(self, project_dir: Path | str | None = None) -> None:
        self.project_dir = Path(project_dir) if project_dir else Path(".")

    def collect(self, days: int = 30) -> DashboardData:
        """Collect and aggregate all metrics.

        Args:
            days: Number of days to include in trends.

        Returns:
            DashboardData with all aggregated metrics.
        """
        data = DashboardData()

        # Collect from each source (best-effort)
        analytics = self._collect_analytics()
        evaluation = self._collect_evaluation(days)
        versioning = self._collect_versioning()
        feedback = self._collect_feedback()
        governance = self._collect_governance()

        # Build system health
        data.system_health = SystemHealth(
            total_agent_runs=analytics.get("total_runs", 0),
            total_workflow_runs=analytics.get("total_workflow_runs", 0),
            total_tokens_used=analytics.get("total_tokens", 0),
            total_content_versions=versioning.get("total_versions", 0),
            active_agents=analytics.get("active_agents", 0),
            avg_quality_score=evaluation.get("avg_score", 0.0),
            overall_pass_rate=evaluation.get("pass_rate", 0.0),
            pending_approvals=governance.get("pending_approvals", 0),
            total_feedback_edits=feedback.get("total_edits", 0),
            learned_patterns=feedback.get("total_patterns", 0),
            audit_entries=governance.get("audit_entries", 0),
            uptime_days=analytics.get("uptime_days", 0.0),
        )

        # Build agent metrics
        data.agent_metrics = self._build_agent_metrics(analytics, evaluation, feedback)

        # Build quality trends
        data.quality_trends = evaluation.get("trends", [])

        # Top agents by usage
        data.top_agents = analytics.get("top_agents", [])

        # Recent activity
        data.recent_activity = self._build_recent_activity(
            versioning, governance, feedback
        )

        return data

    def _collect_analytics(self) -> dict[str, Any]:
        """Collect from analytics system."""
        try:
            from tools.analytics import Analytics

            analytics = Analytics.load()
            summary = analytics.summary()

            total_tokens = 0
            agent_data: dict[str, dict[str, Any]] = {}
            for name, usage in analytics.agents.items():
                tokens = usage.total_input_tokens + usage.total_output_tokens
                total_tokens += tokens
                agent_data[name] = {
                    "runs": usage.run_count,
                    "tokens": tokens,
                    "avg_latency": usage.total_latency_ms / usage.run_count if usage.run_count else 0,
                    "last_used": usage.last_used,
                }

            top_agents = sorted(
                [{"name": k, **v} for k, v in agent_data.items()],
                key=lambda x: x["runs"],
                reverse=True,
            )[:10]

            first_run = analytics.first_run or time.time()
            uptime = (time.time() - first_run) / 86400

            return {
                "total_runs": analytics.total_runs,
                "total_workflow_runs": sum(analytics.workflow_runs.values()),
                "total_tokens": total_tokens,
                "active_agents": len(analytics.agents),
                "top_agents": top_agents,
                "agent_data": agent_data,
                "uptime_days": uptime,
            }
        except Exception:
            return {}

    def _collect_evaluation(self, days: int) -> dict[str, Any]:
        """Collect from evaluation history."""
        try:
            from runtime.evaluation_history import EvaluationHistory

            history = EvaluationHistory(project_dir=self.project_dir)
            cutoff = time.time() - (days * 86400)

            recent = [
                e for e in history.history if e.get("timestamp", 0) > cutoff
            ]

            if not recent:
                return {"avg_score": 0.0, "pass_rate": 0.0, "trends": []}

            scores = [e.get("composite_score", 0) for e in recent]
            passed = sum(1 for e in recent if e.get("passed", False))

            trends = [
                QualityTrend(
                    timestamp=e.get("timestamp", 0),
                    composite_score=e.get("composite_score", 0),
                    agent_slug=e.get("agent_slug", ""),
                    passed=e.get("passed", False),
                )
                for e in recent[-50:]  # Last 50 data points
            ]

            # Per-agent evaluation data
            agent_eval: dict[str, dict[str, Any]] = {}
            for e in recent:
                slug = e.get("agent_slug", "")
                if slug not in agent_eval:
                    agent_eval[slug] = {"scores": [], "passed": 0, "total": 0}
                agent_eval[slug]["scores"].append(e.get("composite_score", 0))
                agent_eval[slug]["total"] += 1
                if e.get("passed"):
                    agent_eval[slug]["passed"] += 1

            return {
                "avg_score": sum(scores) / len(scores),
                "pass_rate": passed / len(recent),
                "trends": trends,
                "agent_eval": agent_eval,
            }
        except Exception:
            return {}

    def _collect_versioning(self) -> dict[str, Any]:
        """Collect from content versioning."""
        try:
            from runtime.versioning import ContentHistory

            history = ContentHistory.load()
            versions = history.versions

            return {
                "total_versions": len(versions),
                "recent_versions": [
                    {
                        "timestamp": v.timestamp,
                        "agent": v.agent_name,
                        "preview": v.output_preview,
                    }
                    for v in versions[-10:]
                ],
            }
        except Exception:
            return {}

    def _collect_feedback(self) -> dict[str, Any]:
        """Collect from feedback loop."""
        try:
            from runtime.feedback_loop import FeedbackStore

            store = FeedbackStore(project_dir=self.project_dir)

            agent_stats: dict[str, dict[str, Any]] = {}
            for edit in store.edits:
                slug = edit.agent_slug
                if slug not in agent_stats:
                    agent_stats[slug] = {"edits": 0, "similarities": []}
                agent_stats[slug]["edits"] += 1
                agent_stats[slug]["similarities"].append(edit.similarity)

            return {
                "total_edits": store.edit_count(),
                "total_patterns": store.pattern_count(),
                "agent_stats": agent_stats,
                "recent_edits": [
                    {
                        "timestamp": e.timestamp,
                        "agent": e.agent_slug,
                        "edit_type": e.edit_type,
                        "similarity": e.similarity,
                    }
                    for e in store.edits[-5:]
                ],
            }
        except Exception:
            return {}

    def _collect_governance(self) -> dict[str, Any]:
        """Collect from governance system."""
        try:
            from runtime.governance import ChangeTracker

            tracker = ChangeTracker(project_dir=self.project_dir)

            return {
                "pending_approvals": tracker.pending_count(),
                "total_changes": tracker.total_count(),
                "audit_entries": tracker.audit_log.count(),
                "recent_changes": [
                    {
                        "timestamp": r.timestamp,
                        "type": r.change_type,
                        "key": r.key,
                        "status": r.approval_status,
                    }
                    for r in tracker.records[-5:]
                ],
            }
        except Exception:
            return {}

    def _build_agent_metrics(
        self,
        analytics: dict[str, Any],
        evaluation: dict[str, Any],
        feedback: dict[str, Any],
    ) -> list[AgentMetrics]:
        """Build per-agent metrics from all sources."""
        agents: dict[str, AgentMetrics] = {}

        # From analytics
        for name, data in analytics.get("agent_data", {}).items():
            slug = name.lower().replace(" ", "-")
            agents[slug] = AgentMetrics(
                slug=slug,
                name=name,
                total_runs=data.get("runs", 0),
                total_tokens=data.get("tokens", 0),
                avg_latency_ms=data.get("avg_latency", 0),
            )

        # From evaluation
        for slug, data in evaluation.get("agent_eval", {}).items():
            if slug not in agents:
                agents[slug] = AgentMetrics(slug=slug)
            scores = data.get("scores", [])
            if scores:
                agents[slug].avg_composite_score = sum(scores) / len(scores)
                agents[slug].recent_scores = scores[-10:]
            total = data.get("total", 0)
            if total:
                agents[slug].pass_rate = data.get("passed", 0) / total

        # From feedback
        for slug, data in feedback.get("agent_stats", {}).items():
            if slug not in agents:
                agents[slug] = AgentMetrics(slug=slug)
            agents[slug].total_edits = data.get("edits", 0)
            sims = data.get("similarities", [])
            if sims:
                agents[slug].avg_edit_similarity = sum(sims) / len(sims)

        return sorted(agents.values(), key=lambda a: a.total_runs, reverse=True)

    def _build_recent_activity(
        self,
        versioning: dict[str, Any],
        governance: dict[str, Any],
        feedback: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Build a unified recent activity feed."""
        activity: list[dict[str, Any]] = []

        for v in versioning.get("recent_versions", []):
            activity.append({
                "type": "content_version",
                "timestamp": v.get("timestamp", 0),
                "description": f"{v.get('agent', '?')}: {v.get('preview', '')[:60]}",
            })

        for c in governance.get("recent_changes", []):
            activity.append({
                "type": "governance",
                "timestamp": c.get("timestamp", 0),
                "description": f"[{c.get('status', '?')}] {c.get('type', '')}: {c.get('key', '')}",
            })

        for e in feedback.get("recent_edits", []):
            activity.append({
                "type": "feedback",
                "timestamp": e.get("timestamp", 0),
                "description": f"Edit ({e.get('edit_type', '?')}): {e.get('agent', '')} "
                              f"(similarity: {e.get('similarity', 0):.0%})",
            })

        return sorted(activity, key=lambda a: a.get("timestamp", 0), reverse=True)[:20]

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self, days: int = 30) -> str:
        """Render dashboard as formatted text for terminal output."""
        data = self.collect(days)
        h = data.system_health

        lines = [
            "=" * 60,
            "  CD AGENCY — OBSERVABILITY DASHBOARD",
            "=" * 60,
            "",
            "SYSTEM HEALTH",
            f"  Agent Runs: {h.total_agent_runs}",
            f"  Workflow Runs: {h.total_workflow_runs}",
            f"  Total Tokens: {h.total_tokens_used:,}",
            f"  Content Versions: {h.total_content_versions}",
            f"  Active Agents: {h.active_agents}",
            f"  Uptime: {h.uptime_days:.1f} days",
            "",
            "QUALITY",
            f"  Avg Quality Score: {h.avg_quality_score:.1f}/100",
            f"  Pass Rate: {h.overall_pass_rate:.0%}",
            "",
            "FEEDBACK & GOVERNANCE",
            f"  Human Edits: {h.total_feedback_edits}",
            f"  Learned Patterns: {h.learned_patterns}",
            f"  Pending Approvals: {h.pending_approvals}",
            f"  Audit Entries: {h.audit_entries}",
        ]

        if data.agent_metrics:
            lines.extend(["", "TOP AGENTS (by usage)"])
            for m in data.agent_metrics[:10]:
                name = m.name or m.slug
                score_str = f"{m.avg_composite_score:.0f}" if m.avg_composite_score else "—"
                pass_str = f"{m.pass_rate:.0%}" if m.pass_rate else "—"
                lines.append(
                    f"  {name:<35} runs={m.total_runs:<5} "
                    f"score={score_str:<5} pass={pass_str}"
                )

        if data.recent_activity:
            lines.extend(["", "RECENT ACTIVITY"])
            for a in data.recent_activity[:10]:
                lines.append(f"  [{a['type']:<18}] {a['description']}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

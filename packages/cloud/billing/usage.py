"""Usage tracking for billing enforcement."""
from __future__ import annotations

import datetime
import uuid
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from .plans import PlanTier, get_plan_limits


class UsageTracker:
    """Tracks and queries resource usage per organisation."""

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------

    @staticmethod
    def track_agent_run(
        org_id: str,
        project_id: str,
        agent_slug: str,
        tokens_used: int,
        model: str,
        session: Session,
    ) -> str:
        """Record a single agent run.  Returns the new ``UsageRecord.id``."""
        from ..database import UsageRecord

        record_id = str(uuid.uuid4())
        record = UsageRecord(
            id=record_id,
            organization_id=org_id,
            project_id=project_id,
            record_type="agent_run",
            agent_slug=agent_slug,
            tokens_used=tokens_used,
            model=model,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(record)
        session.commit()
        return record_id

    @staticmethod
    def track_api_call(
        org_id: str,
        project_id: str,
        session: Session,
    ) -> str:
        """Record a generic API call.  Returns the new ``UsageRecord.id``."""
        from ..database import UsageRecord

        record_id = str(uuid.uuid4())
        record = UsageRecord(
            id=record_id,
            organization_id=org_id,
            project_id=project_id,
            record_type="api_call",
            tokens_used=0,
            created_at=datetime.datetime.utcnow(),
        )
        session.add(record)
        session.commit()
        return record_id

    # ------------------------------------------------------------------
    # Querying helpers
    # ------------------------------------------------------------------

    @staticmethod
    def get_current_usage(org_id: str, session: Session) -> dict[str, Any]:
        """Return usage counts for the current billing period (calendar month).

        Keys returned:
        - ``agent_runs_per_month`` – number of agent runs this month
        - ``tokens_per_month`` – total tokens consumed this month
        - ``api_calls`` – number of API calls this month
        - ``projects`` – total number of projects for the org
        - ``api_keys`` – total number of active API keys for the org
        - ``team_members`` – total number of members for the org
        """
        from ..database import UsageRecord, Project, APIKey, Organization
        from sqlalchemy import func

        now = datetime.datetime.utcnow()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Agent runs this month
        agent_runs: int = (
            session.query(func.count(UsageRecord.id))
            .filter(
                UsageRecord.organization_id == org_id,
                UsageRecord.record_type == "agent_run",
                UsageRecord.created_at >= period_start,
            )
            .scalar()
        ) or 0

        # Tokens this month
        tokens: int = (
            session.query(func.coalesce(func.sum(UsageRecord.tokens_used), 0))
            .filter(
                UsageRecord.organization_id == org_id,
                UsageRecord.created_at >= period_start,
            )
            .scalar()
        ) or 0

        # API calls this month
        api_calls: int = (
            session.query(func.count(UsageRecord.id))
            .filter(
                UsageRecord.organization_id == org_id,
                UsageRecord.record_type == "api_call",
                UsageRecord.created_at >= period_start,
            )
            .scalar()
        ) or 0

        # Total projects (not time-bounded)
        projects: int = (
            session.query(func.count(Project.id))
            .filter(Project.organization_id == org_id)
            .scalar()
        ) or 0

        # Active API keys
        api_keys: int = (
            session.query(func.count(APIKey.id))
            .filter(APIKey.organization_id == org_id)
            .scalar()
        ) or 0

        # Team members
        org = session.query(Organization).filter_by(id=org_id).first()
        team_members: int = getattr(org, "member_count", 1) if org else 0

        return {
            "agent_runs_per_month": agent_runs,
            "tokens_per_month": tokens,
            "api_calls": api_calls,
            "projects": projects,
            "api_keys": api_keys,
            "team_members": team_members,
        }

    @staticmethod
    def is_within_limits(
        org_id: str,
        session: Session,
    ) -> tuple[bool, str | None]:
        """Check whether *org_id* is within all plan limits.

        Returns ``(True, None)`` when within limits, or
        ``(False, reason)`` when a limit has been exceeded.
        """
        from ..database import Subscription

        sub = (
            session.query(Subscription)
            .filter_by(organization_id=org_id, status="active")
            .first()
        )
        tier = PlanTier(sub.plan_tier) if sub else PlanTier.FREE
        limits = get_plan_limits(tier)
        usage = UsageTracker.get_current_usage(org_id, session)

        checks: list[tuple[str, int, int]] = [
            ("agent_runs_per_month", usage["agent_runs_per_month"], limits.agent_runs_per_month),
            ("tokens_per_month", usage["tokens_per_month"], limits.tokens_per_month),
            ("projects", usage["projects"], limits.projects),
            ("api_keys", usage["api_keys"], limits.api_keys),
            ("team_members", usage["team_members"], limits.team_members),
        ]

        for name, current, maximum in checks:
            if maximum == -1:
                continue  # unlimited
            if current >= maximum:
                return False, (
                    f"Limit exceeded for {name}: {current}/{maximum} "
                    f"on {tier.value} plan"
                )

        return True, None

"""Plan definitions and limit checking for CD Agency Cloud."""
from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class PlanTier(str, enum.Enum):
    """Available subscription tiers."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class PlanLimits:
    """Resource limits for a subscription plan.

    A value of ``-1`` means unlimited.
    """

    agent_runs_per_month: int
    projects: int
    api_keys: int
    connectors: int
    team_members: int
    tokens_per_month: int
    priority_support: bool = False


# ---------------------------------------------------------------------------
# Plan catalogue
# ---------------------------------------------------------------------------

PLAN_LIMITS: dict[PlanTier, PlanLimits] = {
    PlanTier.FREE: PlanLimits(
        agent_runs_per_month=50,
        projects=2,
        api_keys=1,
        connectors=1,
        team_members=1,
        tokens_per_month=100_000,
        priority_support=False,
    ),
    PlanTier.STARTER: PlanLimits(
        agent_runs_per_month=500,
        projects=10,
        api_keys=5,
        connectors=5,
        team_members=5,
        tokens_per_month=1_000_000,
        priority_support=False,
    ),
    PlanTier.PRO: PlanLimits(
        agent_runs_per_month=5_000,
        projects=-1,
        api_keys=20,
        connectors=-1,
        team_members=20,
        tokens_per_month=10_000_000,
        priority_support=False,
    ),
    PlanTier.ENTERPRISE: PlanLimits(
        agent_runs_per_month=-1,
        projects=-1,
        api_keys=-1,
        connectors=-1,
        team_members=-1,
        tokens_per_month=-1,
        priority_support=True,
    ),
}


def get_plan_limits(tier: PlanTier) -> PlanLimits:
    """Return the ``PlanLimits`` for the given *tier*."""
    return PLAN_LIMITS[tier]


def check_limit(
    org_id: str,
    limit_type: str,
    session: Session,
) -> tuple[bool, str]:
    """Check whether *org_id* is within its plan limit for *limit_type*.

    Parameters
    ----------
    org_id:
        The organisation identifier.
    limit_type:
        One of the ``PlanLimits`` field names, e.g. ``"agent_runs_per_month"``,
        ``"projects"``, ``"api_keys"``, etc.
    session:
        A SQLAlchemy session used to look up the organisation and its usage.

    Returns
    -------
    tuple[bool, str]
        ``(True, "")`` when within limits, ``(False, reason)`` when the limit
        has been reached.
    """
    from ..database import Organization, Subscription

    org = session.query(Organization).filter_by(id=org_id).first()
    if org is None:
        return False, f"Organization {org_id} not found"

    # Determine the organisation's current plan tier.
    sub = (
        session.query(Subscription)
        .filter_by(organization_id=org_id, status="active")
        .first()
    )
    tier = PlanTier(sub.plan_tier) if sub else PlanTier.FREE

    limits = get_plan_limits(tier)
    max_value: int = getattr(limits, limit_type, None)  # type: ignore[assignment]
    if max_value is None:
        return False, f"Unknown limit type: {limit_type}"

    # Unlimited
    if max_value == -1:
        return True, ""

    # Retrieve current usage for the requested limit type.
    from .usage import UsageTracker

    current_usage = UsageTracker.get_current_usage(org_id, session)
    current_value = current_usage.get(limit_type, 0)

    if current_value >= max_value:
        return False, (
            f"Limit reached for {limit_type}: {current_value}/{max_value} "
            f"on {tier.value} plan"
        )

    return True, ""

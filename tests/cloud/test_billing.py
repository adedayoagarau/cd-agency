"""Tests for billing plans and usage tracking."""
from __future__ import annotations

import pytest


class TestPlanTier:
    def test_plan_values(self):
        from packages.cloud.billing.plans import PlanTier

        assert PlanTier.FREE.value == "free"
        assert PlanTier.STARTER.value == "starter"
        assert PlanTier.PRO.value == "pro"
        assert PlanTier.ENTERPRISE.value == "enterprise"

    def test_plan_tier_from_string(self):
        from packages.cloud.billing.plans import PlanTier

        assert PlanTier("free") == PlanTier.FREE
        assert PlanTier("enterprise") == PlanTier.ENTERPRISE


class TestPlanLimits:
    def test_free_plan_limits(self):
        from packages.cloud.billing.plans import PlanTier, get_plan_limits

        limits = get_plan_limits(PlanTier.FREE)
        assert limits.agent_runs_per_month == 50
        assert limits.projects == 2
        assert limits.api_keys == 1
        assert limits.connectors == 1
        assert limits.team_members == 1
        assert limits.tokens_per_month == 100_000
        assert limits.priority_support is False

    def test_starter_plan_limits(self):
        from packages.cloud.billing.plans import PlanTier, get_plan_limits

        limits = get_plan_limits(PlanTier.STARTER)
        assert limits.agent_runs_per_month == 500
        assert limits.projects == 10
        assert limits.tokens_per_month == 1_000_000

    def test_pro_plan_limits(self):
        from packages.cloud.billing.plans import PlanTier, get_plan_limits

        limits = get_plan_limits(PlanTier.PRO)
        assert limits.agent_runs_per_month == 5_000
        assert limits.projects == -1  # unlimited
        assert limits.connectors == -1
        assert limits.tokens_per_month == 10_000_000

    def test_enterprise_plan_unlimited(self):
        from packages.cloud.billing.plans import PlanTier, get_plan_limits

        limits = get_plan_limits(PlanTier.ENTERPRISE)
        assert limits.agent_runs_per_month == -1
        assert limits.projects == -1
        assert limits.api_keys == -1
        assert limits.connectors == -1
        assert limits.team_members == -1
        assert limits.tokens_per_month == -1
        assert limits.priority_support is True

    def test_plan_limits_are_frozen(self):
        from packages.cloud.billing.plans import PlanTier, get_plan_limits

        limits = get_plan_limits(PlanTier.FREE)
        with pytest.raises(AttributeError):
            limits.agent_runs_per_month = 999  # type: ignore[misc]

    def test_all_plans_defined(self):
        from packages.cloud.billing.plans import PLAN_LIMITS, PlanTier

        for tier in PlanTier:
            assert tier in PLAN_LIMITS

    def test_plan_hierarchy(self):
        from packages.cloud.billing.plans import PlanTier, get_plan_limits

        free = get_plan_limits(PlanTier.FREE)
        starter = get_plan_limits(PlanTier.STARTER)
        pro = get_plan_limits(PlanTier.PRO)

        assert starter.agent_runs_per_month > free.agent_runs_per_month
        assert pro.agent_runs_per_month > starter.agent_runs_per_month
        assert starter.tokens_per_month > free.tokens_per_month
        assert pro.tokens_per_month > starter.tokens_per_month

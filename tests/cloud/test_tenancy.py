"""Tests for multi-tenant context management."""
from __future__ import annotations

import pytest


class TestTenantContext:
    def test_create_context(self):
        from packages.cloud.auth.rbac import Role
        from packages.cloud.tenancy.context import TenantContext

        ctx = TenantContext(org_id="org1", user_id="u1", role=Role.ADMIN)
        assert ctx.org_id == "org1"
        assert ctx.user_id == "u1"
        assert ctx.role == Role.ADMIN
        assert ctx.project_id is None

    def test_create_context_with_project(self):
        from packages.cloud.auth.rbac import Role
        from packages.cloud.tenancy.context import TenantContext

        ctx = TenantContext(
            org_id="org1", user_id="u1", role=Role.EDITOR, project_id="proj1"
        )
        assert ctx.project_id == "proj1"

    def test_context_is_frozen(self):
        from packages.cloud.auth.rbac import Role
        from packages.cloud.tenancy.context import TenantContext

        ctx = TenantContext(org_id="org1", user_id="u1", role=Role.VIEWER)
        with pytest.raises(AttributeError):
            ctx.org_id = "org2"  # type: ignore[misc]

    def test_get_without_set_raises(self):
        from packages.cloud.tenancy.context import get_current_tenant

        # Run in a fresh context (no tenant set)
        import contextvars
        ctx_copy = contextvars.copy_context()
        with pytest.raises(LookupError, match="No tenant"):
            ctx_copy.run(get_current_tenant)

    def test_set_and_get_tenant(self):
        from packages.cloud.auth.rbac import Role
        from packages.cloud.tenancy.context import (
            TenantContext,
            get_current_tenant,
            set_current_tenant,
            tenant_scope,
        )

        ctx = TenantContext(org_id="org1", user_id="u1", role=Role.OWNER)
        with tenant_scope(ctx):
            retrieved = get_current_tenant()
            assert retrieved.org_id == "org1"
            assert retrieved.role == Role.OWNER

    def test_tenant_scope_resets(self):
        from packages.cloud.auth.rbac import Role
        from packages.cloud.tenancy.context import TenantContext, tenant_scope

        import contextvars

        ctx = TenantContext(org_id="org1", user_id="u1", role=Role.ADMIN)

        def run_in_scope():
            with tenant_scope(ctx) as t:
                assert t.org_id == "org1"
            # After scope, tenant should be reset
            from packages.cloud.tenancy.context import get_current_tenant
            with pytest.raises(LookupError):
                get_current_tenant()

        # Run in a clean context
        contextvars.copy_context().run(run_in_scope)

    def test_nested_tenant_scopes(self):
        from packages.cloud.auth.rbac import Role
        from packages.cloud.tenancy.context import (
            TenantContext,
            get_current_tenant,
            tenant_scope,
        )

        ctx1 = TenantContext(org_id="org1", user_id="u1", role=Role.ADMIN)
        ctx2 = TenantContext(org_id="org2", user_id="u2", role=Role.VIEWER)

        with tenant_scope(ctx1):
            assert get_current_tenant().org_id == "org1"
            with tenant_scope(ctx2):
                assert get_current_tenant().org_id == "org2"
            assert get_current_tenant().org_id == "org1"

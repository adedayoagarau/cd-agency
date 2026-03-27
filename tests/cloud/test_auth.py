"""Tests for cloud auth module — API keys, RBAC, Clerk JWT."""
from __future__ import annotations

import hashlib
import secrets
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# API key generation and parsing
# ---------------------------------------------------------------------------


class TestAPIKeyGeneration:
    def test_generate_api_key_format(self):
        from packages.cloud.auth.api_keys import generate_api_key

        full_key, prefix, key_hash = generate_api_key()
        assert full_key.startswith("cda_")
        parts = full_key.split("_")
        assert len(parts) == 3
        assert parts[0] == "cda"
        assert len(parts[1]) == 8  # prefix
        assert len(parts[2]) == 32  # secret

    def test_generate_unique_keys(self):
        from packages.cloud.auth.api_keys import generate_api_key

        keys = {generate_api_key()[0] for _ in range(10)}
        assert len(keys) == 10

    def test_key_hash_is_sha256(self):
        from packages.cloud.auth.api_keys import generate_api_key

        full_key, prefix, key_hash = generate_api_key()
        secret = full_key.split("_")[2]
        expected_hash = hashlib.sha256(secret.encode()).hexdigest()
        assert key_hash == expected_hash

    def test_parse_valid_key(self):
        from packages.cloud.auth.api_keys import generate_api_key, parse_api_key

        full_key, prefix, _ = generate_api_key()
        parsed_prefix, parsed_secret = parse_api_key(full_key)
        assert parsed_prefix == prefix
        assert len(parsed_secret) == 32

    def test_parse_invalid_format(self):
        from packages.cloud.auth.api_keys import parse_api_key

        with pytest.raises(ValueError, match="Invalid API key"):
            parse_api_key("invalid-key-format")

    def test_parse_wrong_prefix(self):
        from packages.cloud.auth.api_keys import parse_api_key

        with pytest.raises(ValueError, match="Invalid API key"):
            parse_api_key("xyz_abcdefgh_" + "a" * 32)

    def test_parse_wrong_prefix_length(self):
        from packages.cloud.auth.api_keys import parse_api_key

        with pytest.raises(ValueError, match="prefix"):
            parse_api_key("cda_short_" + "a" * 32)

    def test_parse_wrong_secret_length(self):
        from packages.cloud.auth.api_keys import parse_api_key

        with pytest.raises(ValueError, match="secret"):
            parse_api_key("cda_abcdefgh_short")


class TestAPIKeyVerification:
    def test_verify_invalid_format_returns_none(self):
        from packages.cloud.auth.api_keys import verify_api_key

        session = MagicMock()
        result = verify_api_key("bad-key", session)
        assert result is None

    def test_verify_not_found_returns_none(self):
        from packages.cloud.auth.api_keys import generate_api_key, verify_api_key

        full_key, _, _ = generate_api_key()
        session = MagicMock()
        session.execute.return_value.fetchone.return_value = None
        result = verify_api_key(full_key, session)
        assert result is None


# ---------------------------------------------------------------------------
# RBAC
# ---------------------------------------------------------------------------


class TestRBAC:
    def test_viewer_has_read(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        assert has_permission(Role.VIEWER, Permission.READ) is True

    def test_viewer_cannot_write(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        assert has_permission(Role.VIEWER, Permission.WRITE) is False

    def test_editor_has_write(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        assert has_permission(Role.EDITOR, Permission.WRITE) is True

    def test_editor_cannot_delete(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        assert has_permission(Role.EDITOR, Permission.DELETE) is False

    def test_admin_has_delete(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        assert has_permission(Role.ADMIN, Permission.DELETE) is True

    def test_admin_cannot_manage_billing(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        assert has_permission(Role.ADMIN, Permission.MANAGE_BILLING) is False

    def test_owner_has_all_permissions(self):
        from packages.cloud.auth.rbac import Permission, Role, has_permission

        for perm in Permission:
            assert has_permission(Role.OWNER, perm) is True

    def test_role_enum_values(self):
        from packages.cloud.auth.rbac import Role

        assert Role.VIEWER.value == "viewer"
        assert Role.EDITOR.value == "editor"
        assert Role.ADMIN.value == "admin"
        assert Role.OWNER.value == "owner"

    def test_permission_enum_values(self):
        from packages.cloud.auth.rbac import Permission

        assert Permission.READ.value == "read"
        assert Permission.MANAGE_BILLING.value == "manage_billing"

    def test_require_permission_decorator(self):
        from packages.cloud.auth.rbac import Permission, Role, require_permission
        from packages.cloud.tenancy.context import TenantContext, tenant_scope

        @require_permission(Permission.WRITE)
        def do_write():
            return "written"

        ctx = TenantContext(org_id="org1", user_id="user1", role=Role.EDITOR)
        with tenant_scope(ctx):
            assert do_write() == "written"

    def test_require_permission_denied(self):
        from packages.cloud.auth.rbac import Permission, Role, require_permission
        from packages.cloud.tenancy.context import TenantContext, tenant_scope

        @require_permission(Permission.DELETE)
        def do_delete():
            return "deleted"

        ctx = TenantContext(org_id="org1", user_id="user1", role=Role.VIEWER)
        with tenant_scope(ctx):
            with pytest.raises(PermissionError, match="lacks"):
                do_delete()

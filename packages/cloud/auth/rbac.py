from __future__ import annotations

import enum
import functools
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class Role(enum.Enum):
    """Organisation-level roles, ordered by increasing privilege."""

    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"


class Permission(enum.Enum):
    """Fine-grained permissions checked by the RBAC layer."""

    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_MEMBERS = "manage_members"
    MANAGE_BILLING = "manage_billing"
    MANAGE_API_KEYS = "manage_api_keys"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VIEWER: {
        Permission.READ,
    },
    Role.EDITOR: {
        Permission.READ,
        Permission.WRITE,
    },
    Role.ADMIN: {
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.MANAGE_MEMBERS,
        Permission.MANAGE_API_KEYS,
    },
    Role.OWNER: {
        Permission.READ,
        Permission.WRITE,
        Permission.DELETE,
        Permission.MANAGE_MEMBERS,
        Permission.MANAGE_BILLING,
        Permission.MANAGE_API_KEYS,
    },
}


def has_permission(role: Role, permission: Permission) -> bool:
    """Return ``True`` if *role* grants *permission*."""
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission) -> Callable[[F], F]:
    """Decorator factory that checks the current tenant's role for *permission*.

    The decorated function will raise ``PermissionError`` if the active
    :class:`~tenancy.context.TenantContext` does not carry a role that
    includes the requested permission.

    Usage::

        @require_permission(Permission.WRITE)
        def update_content(...):
            ...
    """

    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from packages.cloud.tenancy.context import get_current_tenant

            tenant = get_current_tenant()
            if not has_permission(tenant.role, permission):
                raise PermissionError(
                    f"Role '{tenant.role.value}' lacks '{permission.value}' permission"
                )
            return fn(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

from packages.cloud.auth.rbac import Role

_tenant_ctx: contextvars.ContextVar[TenantContext] = contextvars.ContextVar(
    "tenant_ctx"
)


@dataclass(frozen=True)
class TenantContext:
    """Immutable context identifying the current tenant and user."""

    org_id: str
    user_id: str
    role: Role
    project_id: str | None = None


def get_current_tenant() -> TenantContext:
    """Return the :class:`TenantContext` for the current execution context.

    Raises ``LookupError`` if no tenant has been set.
    """
    try:
        return _tenant_ctx.get()
    except LookupError:
        raise LookupError("No tenant context has been set for this scope")


def set_current_tenant(ctx: TenantContext) -> contextvars.Token[TenantContext]:
    """Set the :class:`TenantContext` and return a reset token."""
    return _tenant_ctx.set(ctx)


@contextmanager
def tenant_scope(ctx: TenantContext) -> Generator[TenantContext, None, None]:
    """Context manager that sets the tenant for the enclosed block.

    Usage::

        with tenant_scope(TenantContext(org_id="org_1", ...)) as t:
            # all code here sees t as the current tenant
            ...
    """
    token = set_current_tenant(ctx)
    try:
        yield ctx
    finally:
        _tenant_ctx.reset(token)

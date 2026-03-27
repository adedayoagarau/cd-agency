"""Dependency injection utilities for the FastAPI application."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncGenerator, Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from packages.cloud.auth import verify_clerk_token, verify_api_key
from packages.cloud.database import SessionLocal


# ---------------------------------------------------------------------------
# CurrentUser dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class CurrentUser:
    """Represents the authenticated user extracted from a token or API key."""

    user_id: str
    org_id: str
    role: str
    email: str


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session and ensure it is closed after the request."""
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> CurrentUser:
    """Extract the current user from a Bearer token or API key.

    Checks the ``Authorization`` header for a Bearer token first, then falls
    back to the ``X-API-Key`` header.  Raises *401* if neither is present or
    valid.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")
        try:
            claims = await verify_clerk_token(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid bearer token: {exc}",
            ) from exc

        return CurrentUser(
            user_id=claims["sub"],
            org_id=claims.get("org_id", ""),
            role=claims.get("role", "member"),
            email=claims.get("email", ""),
        )

    if x_api_key:
        try:
            key_data = await verify_api_key(x_api_key)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid API key: {exc}",
            ) from exc

        return CurrentUser(
            user_id=key_data["user_id"],
            org_id=key_data["org_id"],
            role=key_data.get("role", "member"),
            email=key_data.get("email", ""),
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication credentials. Provide a Bearer token or X-API-Key header.",
    )


# ---------------------------------------------------------------------------
# Role-checking dependency factory
# ---------------------------------------------------------------------------

def require_role(role: str) -> Callable[..., CurrentUser]:
    """Return a FastAPI dependency that ensures the user has the given *role*.

    Usage::

        @router.get("/admin-only")
        async def admin_endpoint(user: CurrentUser = Depends(require_role("admin"))):
            ...
    """

    async def _check_role(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        # Simple hierarchy: admin > editor > member
        hierarchy = {"admin": 3, "editor": 2, "member": 1}
        required_level = hierarchy.get(role, 0)
        user_level = hierarchy.get(user.role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required. Your role: '{user.role}'.",
            )
        return user

    return _check_role

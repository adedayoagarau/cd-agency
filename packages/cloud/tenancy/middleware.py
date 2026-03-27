from __future__ import annotations

import json
from typing import Any, Callable

from packages.cloud.auth.api_keys import APIKey, parse_api_key, verify_api_key
from packages.cloud.auth.clerk import ClerkAuthConfig, verify_clerk_token
from packages.cloud.auth.rbac import Role
from packages.cloud.tenancy.context import TenantContext, set_current_tenant

# ASGI type aliases
Scope = dict[str, Any]
Receive = Callable[..., Any]
Send = Callable[..., Any]


class TenantMiddleware:
    """ASGI middleware that extracts tenant identity from every request.

    Supports two authentication strategies (checked in order):
    1. **Bearer JWT** (``Authorization: Bearer <token>``) -- verified via Clerk.
    2. **API key** (``X-API-Key: cda_...``) -- looked up in the database.

    On success the middleware:
    - Sets a :class:`TenantContext` in ``contextvars`` for the request lifetime.
    - Stores ``org_id`` on ``scope["state"]`` so downstream handlers can read
      it without importing the context helpers.

    On failure it returns a ``401 Unauthorized`` JSON response.
    """

    def __init__(
        self,
        app: Any,
        *,
        clerk_config: ClerkAuthConfig | None = None,
        db_session_factory: Callable[..., Any] | None = None,
        public_paths: set[str] | None = None,
    ) -> None:
        self.app = app
        self.clerk_config = clerk_config or ClerkAuthConfig()
        self.db_session_factory = db_session_factory
        self.public_paths: set[str] = public_paths or {"/health", "/docs", "/openapi.json"}

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path in self.public_paths:
            await self.app(scope, receive, send)
            return

        headers = dict(self._parse_headers(scope))

        tenant = self._authenticate_bearer(headers)
        if tenant is None:
            tenant = self._authenticate_api_key(headers)

        if tenant is None:
            await self._send_401(send)
            return

        token = set_current_tenant(tenant)
        try:
            # Expose org_id on ASGI scope state for convenience
            scope.setdefault("state", {})
            scope["state"]["org_id"] = tenant.org_id
            scope["state"]["user_id"] = tenant.user_id

            await self.app(scope, receive, send)
        finally:
            from packages.cloud.tenancy.context import _tenant_ctx

            _tenant_ctx.reset(token)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_headers(scope: Scope) -> list[tuple[str, str]]:
        """Return headers as a list of lowercase ``(name, value)`` pairs."""
        raw: list[tuple[bytes, bytes]] = scope.get("headers", [])
        return [(k.decode().lower(), v.decode()) for k, v in raw]

    def _authenticate_bearer(self, headers: dict[str, str]) -> TenantContext | None:
        auth = headers.get("authorization", "")
        if not auth.lower().startswith("bearer "):
            return None

        token_str = auth[7:].strip()
        try:
            claims = verify_clerk_token(token_str, self.clerk_config)
        except (ValueError, Exception):
            return None

        org_id = claims.get("org_id", claims.get("sub", ""))
        user_id = claims.get("sub", "")
        role_str = claims.get("org_role", claims.get("role", "viewer"))

        try:
            role = Role(role_str)
        except ValueError:
            role = Role.VIEWER

        return TenantContext(
            org_id=org_id,
            user_id=user_id,
            role=role,
        )

    def _authenticate_api_key(self, headers: dict[str, str]) -> TenantContext | None:
        api_key = headers.get("x-api-key", "")
        if not api_key:
            return None

        if self.db_session_factory is None:
            return None

        session = self.db_session_factory()
        try:
            record: APIKey | None = verify_api_key(api_key, session)
        except Exception:
            return None
        finally:
            if hasattr(session, "close"):
                session.close()

        if record is None:
            return None

        return TenantContext(
            org_id=record.org_id,
            user_id=record.created_by,
            role=Role.EDITOR,  # API keys default to EDITOR; refine via scopes later
        )

    @staticmethod
    async def _send_401(send: Send) -> None:
        body = json.dumps({"detail": "Unauthorized"}).encode()
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )

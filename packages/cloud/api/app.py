"""FastAPI application factory for CD Agency Cloud."""
from __future__ import annotations

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .routes.agents import router as agents_router
from .routes.projects import router as projects_router
from .routes.auth import router as auth_router
from .routes.billing import router as billing_router
from .routes.connectors import router as connectors_router
from .routes.websocket import router as websocket_router


# ---------------------------------------------------------------------------
# Tenant middleware
# ---------------------------------------------------------------------------

class TenantMiddleware(BaseHTTPMiddleware):
    """Extract tenant/org information from the request and attach to state."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Tenant ID may come from a header, token claim, or API key lookup.
        # The actual resolution happens inside get_current_user; here we just
        # ensure the state attribute exists so downstream code can rely on it.
        request.state.org_id = None
        response = await call_next(request)
        return response


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app(
    *,
    cors_origins: list[str] | None = None,
    title: str = "CD Agency Cloud API",
    version: str = "2.0.0",
) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    cors_origins:
        Allowed CORS origins.  Defaults to ``["*"]`` for development.
    title:
        OpenAPI title.
    version:
        API version string.
    """
    app = FastAPI(
        title=title,
        version=version,
        docs_url="/v2/docs",
        redoc_url="/v2/redoc",
        openapi_url="/v2/openapi.json",
    )

    # -- CORS ---------------------------------------------------------------
    allowed_origins = cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -- Tenant middleware ---------------------------------------------------
    app.add_middleware(TenantMiddleware)

    # -- Routers ------------------------------------------------------------
    app.include_router(agents_router)
    app.include_router(projects_router)
    app.include_router(auth_router)
    app.include_router(billing_router)
    app.include_router(connectors_router)
    app.include_router(websocket_router)

    # -- Health & version ---------------------------------------------------
    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v2", tags=["system"])
    async def api_version() -> dict[str, str]:
        return {"version": version, "api": "v2"}

    return app

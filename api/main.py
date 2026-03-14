"""FastAPI application for the CD Agency REST API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers import agents, history, presets, scoring, validate
from api.routers import export as export_router
from api.routers import scrape, workflows

app = FastAPI(
    title="CD Agency API",
    description="Content Design Agency — REST API for UX writing, content scoring, and design system presets.",
    version="0.5.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow all origins so the Figma plugin and external integrations can connect.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(agents.router, prefix="/api/v1")
app.include_router(scoring.router, prefix="/api/v1")
app.include_router(presets.router, prefix="/api/v1")
app.include_router(validate.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")
app.include_router(workflows.router, prefix="/api/v1")
app.include_router(scrape.router, prefix="/api/v1")
app.include_router(export_router.router, prefix="/api/v1")


# ── Health Check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and uptime monitors."""
    return {"status": "ok"}


# ── Static Files (SPA) ──────────────────────────────────────────────────────

WEB_DIST = Path(__file__).parent.parent / "web" / "dist"

if WEB_DIST.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        """Serve the React SPA — fallback to index.html for client-side routing."""
        file_path = WEB_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(WEB_DIST / "index.html")

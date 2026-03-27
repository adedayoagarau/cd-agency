"""FastAPI application for the CD Agency REST API."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers import agents, history, presets, scoring, validate
from api.routers import export as export_router
from api.routers import scrape, workflows
from api.routers.v2 import agents as agents_v2
from api.routers.v2 import brand_dna as brand_dna_v2
from api.routers.v2 import memory as memory_v2
from api.routers.v2 import connectors as connectors_v2
from api.routers.v2 import history as history_v2
from api.routers.v2 import config as config_v2
from api.routers.v2 import websocket as websocket_v2
from api.routers.v2 import scoring as scoring_v2
from api.routers.v2 import workflows as workflows_v2
from api.routers.v2 import presets as presets_v2
from api.routers.v2 import validate as validate_v2
from api.routers.v2 import scrape as scrape_v2
from api.routers.v2 import export as export_v2

app = FastAPI(
    title="CD Agency API",
    description="Content Design Agency — REST API for UX writing, content scoring, and design system presets.",
    version="0.6.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

# ── V2 Routers ──────────────────────────────────────────────────────────────

app.include_router(agents_v2.router)
app.include_router(brand_dna_v2.router)
app.include_router(memory_v2.router)
app.include_router(connectors_v2.router)
app.include_router(history_v2.router)
app.include_router(config_v2.router)
app.include_router(websocket_v2.router)
app.include_router(scoring_v2.router)
app.include_router(workflows_v2.router)
app.include_router(presets_v2.router)
app.include_router(validate_v2.router)
app.include_router(scrape_v2.router)
app.include_router(export_v2.router)


# ── Health Check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and uptime monitors."""
    import importlib.metadata
    try:
        version = importlib.metadata.version("cd-agency")
    except Exception:
        version = "0.6.0"
    return {"status": "ok", "version": version}


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

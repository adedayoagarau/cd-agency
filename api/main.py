"""FastAPI application for the CD Agency REST API."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import agents, history, presets, scoring, validate

app = FastAPI(
    title="CD Agency API",
    description="Content Design Agency — REST API for UX writing, content scoring, and design system presets.",
    version="0.4.0",
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


# ── Health Check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and uptime monitors."""
    return {"status": "ok"}

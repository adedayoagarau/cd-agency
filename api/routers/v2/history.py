from __future__ import annotations
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from runtime.versioning import ContentHistory

router = APIRouter(prefix="/api/v2/history", tags=["history-v2"])


# ── Models ───────────────────────────────────────────────────────────────────


class VersionResponseV2(BaseModel):
    id: str
    timestamp: float
    agent_name: str
    agent_slug: str
    input_text: str
    output_text: str
    input_fields: dict[str, str] = {}
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


class HistoryStatsResponseV2(BaseModel):
    count: int
    agents_used: list[str]
    latest: dict[str, Any] | None = None


# ── Helpers ──────────────────────────────────────────────────────────────────


def _version_to_response(v) -> VersionResponseV2:
    return VersionResponseV2(
        id=v.id,
        timestamp=v.timestamp,
        agent_name=v.agent_name,
        agent_slug=v.agent_slug,
        input_text=v.input_text,
        output_text=v.output_text,
        input_fields=v.input_fields,
        model=v.model,
        input_tokens=v.input_tokens,
        output_tokens=v.output_tokens,
        latency_ms=v.latency_ms,
    )


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("")
async def get_history(
    agent: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
):
    """List recent evaluation history entries with optional filtering."""
    from runtime.evaluation_history import EvaluationHistory
    try:
        eval_history = EvaluationHistory()
        all_entries = eval_history.history  # This is a list[dict]

        filtered = all_entries
        if agent:
            filtered = [e for e in filtered if e.get("agent_slug") == agent]
        if status:
            if status == "passed":
                filtered = [e for e in filtered if e.get("passed", False)]
            elif status == "failed":
                filtered = [e for e in filtered if not e.get("passed", True)]

        total = len(filtered)
        # Sort by timestamp descending (most recent first)
        filtered.sort(key=lambda e: e.get("timestamp", 0), reverse=True)
        page = filtered[offset:offset + limit]

        runs = []
        for entry in page:
            ts = entry.get("timestamp", 0)
            # Format timestamp as ISO string if it's a float
            if isinstance(ts, (int, float)):
                from datetime import datetime, timezone
                ts = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            runs.append({
                "agent_slug": entry.get("agent_slug", ""),
                "composite_score": entry.get("composite_score", 0.0),
                "passed": entry.get("passed", False),
                "iteration_count": entry.get("iteration_count", 1),
                "timestamp": str(ts),
                "scores": entry.get("scores", {}),
            })

        return {"runs": runs, "total": total}
    except Exception:
        return {"runs": [], "total": 0}


@router.get("/stats", response_model=HistoryStatsResponseV2)
async def history_stats() -> HistoryStatsResponseV2:
    """Get aggregate content versioning statistics."""
    try:
        hist = ContentHistory.load()
        summary = hist.summary()
        return HistoryStatsResponseV2(**summary)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load history stats: {exc}")


@router.get("/search", response_model=list[VersionResponseV2])
async def search_history(
    q: str = Query(..., min_length=1, description="Search query"),
) -> list[VersionResponseV2]:
    """Search content history by input or output text."""
    try:
        hist = ContentHistory.load()
        results = hist.search(q)
        return [_version_to_response(v) for v in results[-20:]]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"History search failed: {exc}")


@router.get("/{version_id}", response_model=VersionResponseV2)
async def get_version(version_id: str) -> VersionResponseV2:
    """Get a specific content version with full before/after."""
    try:
        hist = ContentHistory.load()
        v = hist.get(version_id)
        if not v:
            raise HTTPException(
                status_code=404,
                detail=f"Version '{version_id}' not found",
            )
        return _version_to_response(v)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to get version: {exc}")

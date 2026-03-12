"""Content history endpoints — browse, search, and diff version history."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.deps import verify_api_key
from api.models import HistoryStatsResponse, VersionDiffResponse, VersionResponse
from runtime.versioning import ContentHistory

router = APIRouter(prefix="/history", tags=["history"])


def _version_to_response(v) -> VersionResponse:
    return VersionResponse(
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


@router.get("", response_model=list[VersionResponse])
async def list_history(
    agent: Annotated[str | None, Query(description="Filter by agent slug")] = None,
    count: Annotated[int, Query(ge=1, le=100, description="Number of versions")] = 20,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> list[VersionResponse]:
    """List recent content versions."""
    hist = ContentHistory.load()
    if agent:
        versions = hist.list_by_agent(agent)[-count:]
        versions = list(reversed(versions))
    else:
        versions = hist.list_recent(count)
    return [_version_to_response(v) for v in versions]


@router.get("/stats", response_model=HistoryStatsResponse)
async def history_stats(
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> HistoryStatsResponse:
    """Get aggregate content versioning statistics."""
    hist = ContentHistory.load()
    summary = hist.summary()
    return HistoryStatsResponse(**summary)


@router.get("/search", response_model=list[VersionResponse])
async def search_history(
    q: Annotated[str, Query(min_length=1, description="Search query")],
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> list[VersionResponse]:
    """Search content history by input or output text."""
    hist = ContentHistory.load()
    results = hist.search(q)
    return [_version_to_response(v) for v in results[-20:]]


@router.get("/{version_id}", response_model=VersionResponse)
async def get_version(
    version_id: str,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> VersionResponse:
    """Get a specific content version with full before/after."""
    hist = ContentHistory.load()
    v = hist.get(version_id)
    if not v:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_id}' not found",
        )
    return _version_to_response(v)


@router.get("/{version_id}/diff", response_model=VersionDiffResponse)
async def diff_version(
    version_id: str,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> VersionDiffResponse:
    """Get a compact before/after diff for a content version."""
    hist = ContentHistory.load()
    d = hist.diff(version_id)
    if not d:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_id}' not found",
        )
    return VersionDiffResponse(**d)

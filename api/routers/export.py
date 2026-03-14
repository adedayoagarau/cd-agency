"""Export endpoint — convert content entries to multiple formats."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse

from api.deps import verify_api_key
from api.models import ExportRequest
from tools.export import ContentEntry, ExportFormat, export_entries

router = APIRouter(prefix="/export", tags=["export"])

FORMAT_MAP = {
    "json": ExportFormat.JSON,
    "csv": ExportFormat.CSV,
    "markdown": ExportFormat.MARKDOWN,
    "xliff": ExportFormat.XLIFF,
}

CONTENT_TYPE_MAP = {
    "json": "application/json",
    "csv": "text/csv",
    "markdown": "text/markdown",
    "xliff": "application/xliff+xml",
}


@router.post("")
async def export_content(
    body: ExportRequest,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> PlainTextResponse:
    """Export content entries in the specified format.

    Supported formats: json, csv, markdown, xliff.
    No API key required (no LLM call).
    """
    fmt = FORMAT_MAP.get(body.format.lower())
    if fmt is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported format: '{body.format}'. Use: json, csv, markdown, xliff",
        )

    entries = [
        ContentEntry(
            id=e.id or f"entry-{i+1}",
            source=e.source,
            target=e.target,
            context=e.context,
            agent=e.agent,
            notes=e.notes,
        )
        for i, e in enumerate(body.entries)
    ]

    result = export_entries(entries, fmt)
    content_type = CONTENT_TYPE_MAP.get(body.format.lower(), "text/plain")

    return PlainTextResponse(content=result, media_type=content_type)


@router.get("/formats")
async def list_formats(
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> list[dict[str, str]]:
    """List available export formats."""
    return [
        {"id": "json", "label": "JSON", "extension": ".json"},
        {"id": "csv", "label": "CSV", "extension": ".csv"},
        {"id": "markdown", "label": "Markdown", "extension": ".md"},
        {"id": "xliff", "label": "XLIFF 1.2", "extension": ".xliff"},
    ]

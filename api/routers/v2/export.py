"""V2 Export endpoints — convert content entries to multiple formats."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from tools.export import ContentEntry, ExportFormat, export_entries

router = APIRouter(prefix="/api/v2/export", tags=["export-v2"])

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


# ── Models ───────────────────────────────────────────────────────────────────


class ExportEntryV2(BaseModel):
    id: str = ""
    source: str
    target: str
    context: str = ""
    agent: str = ""
    notes: str = ""


class ExportRequestV2(BaseModel):
    entries: list[ExportEntryV2] = Field(..., min_length=1)
    format: str = Field(..., description="Export format: json, csv, markdown, xliff")


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("")
async def export_content(body: ExportRequestV2) -> PlainTextResponse:
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

    try:
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {exc}",
        )


@router.get("/formats")
async def list_formats() -> list[dict[str, str]]:
    """List available export formats."""
    return [
        {"id": "json", "label": "JSON", "extension": ".json"},
        {"id": "csv", "label": "CSV", "extension": ".csv"},
        {"id": "markdown", "label": "Markdown", "extension": ".md"},
        {"id": "xliff", "label": "XLIFF 1.2", "extension": ".xliff"},
    ]

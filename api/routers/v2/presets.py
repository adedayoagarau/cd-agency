"""V2 Preset endpoints — list and detail for design system voice profiles."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

import yaml

from api.deps import PRESETS_DIR

router = APIRouter(prefix="/api/v2/presets", tags=["presets-v2"])


# ── Models ───────────────────────────────────────────────────────────────────


class PresetSummaryV2(BaseModel):
    name: str
    filename: str


class PresetDetailV2(BaseModel):
    name: str
    filename: str
    tone_descriptors: list[str] = []
    do_rules: list[str] = []
    dont_rules: list[str] = []
    sample_content: list[str] = []
    character_limits: dict[str, int] = {}
    terminology: dict[str, str] = {}


# ── Helpers ──────────────────────────────────────────────────────────────────


def _load_preset_files() -> dict[str, dict]:
    """Load all YAML preset files from the presets/ directory."""
    presets: dict[str, dict] = {}
    if not PRESETS_DIR.is_dir():
        return presets

    for path in sorted(PRESETS_DIR.glob("*.yaml")):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        data["_filename"] = path.stem
        presets[path.stem] = data
    return presets


# ── Routes ───────────────────────────────────────────────────────────────────


@router.get("", response_model=list[PresetSummaryV2])
async def list_presets() -> list[PresetSummaryV2]:
    """List all available design system presets."""
    try:
        presets = _load_preset_files()
        return [
            PresetSummaryV2(
                name=data.get("name", filename),
                filename=filename,
            )
            for filename, data in presets.items()
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load presets: {exc}",
        )


@router.get("/{name}", response_model=PresetDetailV2)
async def get_preset(name: str) -> PresetDetailV2:
    """Get full details for a design system preset by filename stem."""
    presets = _load_preset_files()

    # Look up by filename stem first, then by display name
    data = presets.get(name)
    if data is None:
        for _filename, pdata in presets.items():
            if pdata.get("name", "").lower() == name.lower():
                data = pdata
                break

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{name}' not found",
        )

    return PresetDetailV2(
        name=data.get("name", data.get("_filename", name)),
        filename=data.get("_filename", name),
        tone_descriptors=data.get("tone_descriptors", []),
        do_rules=data.get("do", []),
        dont_rules=data.get("dont", []),
        sample_content=data.get("sample_content", []),
        character_limits=data.get("character_limits", {}),
        terminology=data.get("terminology", {}),
    )

"""V2 Validation endpoints — UI constraint checking for content."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from runtime.constraints import list_element_types, validate_content

router = APIRouter(prefix="/api/v2/validate", tags=["validation-v2"])


# ── Models ───────────────────────────────────────────────────────────────────


class ValidateRequestV2(BaseModel):
    text: str = Field(..., min_length=1, description="Text content to validate")
    element_type: str = Field(..., description="UI element type (e.g., 'button', 'toast', 'push_body')")
    platform: str | None = Field(None, description="Target platform: ios, android, web")
    target_language: str | None = Field(None, description="ISO language code for localization check (e.g., 'de', 'fr')")
    custom_limit: int | None = Field(None, description="Override the default character limit")


class ViolationResponseV2(BaseModel):
    rule: str
    severity: str
    message: str
    value: Any = None
    limit: Any = None


class ValidateResponseV2(BaseModel):
    passed: bool
    error_count: int
    warning_count: int
    violations: list[ViolationResponseV2]
    summary: str


class ElementTypeInfoV2(BaseModel):
    type: str
    max_chars: int
    label: str


# ── Routes ───────────────────────────────────────────────────────────────────


@router.post("", response_model=ValidateResponseV2)
async def validate(body: ValidateRequestV2) -> ValidateResponseV2:
    """Validate UI text against character limits, platform conventions, a11y, and localization expansion."""
    try:
        result = validate_content(
            body.text,
            body.element_type,
            platform=body.platform,
            target_language=body.target_language,
            custom_limit=body.custom_limit,
        )
        violations = [
            ViolationResponseV2(
                rule=v.rule,
                severity=v.severity,
                message=v.message,
                value=v.value,
                limit=v.limit,
            )
            for v in result.violations
        ]
        return ValidateResponseV2(
            passed=result.passed,
            error_count=len(result.errors),
            warning_count=len(result.warnings),
            violations=violations,
            summary=result.summary(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {exc}",
        )


@router.get("/element-types", response_model=list[ElementTypeInfoV2])
async def get_element_types() -> list[ElementTypeInfoV2]:
    """List all supported UI element types and their default character limits."""
    try:
        return [ElementTypeInfoV2(**et) for et in list_element_types()]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list element types: {exc}",
        )

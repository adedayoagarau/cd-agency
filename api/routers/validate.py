"""Validation endpoints — UI constraint checking for content."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.deps import verify_api_key
from api.models import (
    ElementTypeInfo,
    ValidateRequest,
    ValidateResponse,
    ViolationResponse,
)
from runtime.constraints import list_element_types, validate_content

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("", response_model=ValidateResponse)
async def validate(
    body: ValidateRequest,
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> ValidateResponse:
    """Validate UI text against character limits, platform conventions, a11y, and localization expansion."""
    result = validate_content(
        body.text,
        body.element_type,
        platform=body.platform,
        target_language=body.target_language,
        custom_limit=body.custom_limit,
    )
    violations = [
        ViolationResponse(
            rule=v.rule,
            severity=v.severity,
            message=v.message,
            value=v.value,
            limit=v.limit,
        )
        for v in result.violations
    ]
    return ValidateResponse(
        passed=result.passed,
        error_count=len(result.errors),
        warning_count=len(result.warnings),
        violations=violations,
        summary=result.summary(),
    )


@router.get("/element-types", response_model=list[ElementTypeInfo])
async def get_element_types(
    _auth: Annotated[str | None, Depends(verify_api_key)] = None,
) -> list[ElementTypeInfo]:
    """List all supported UI element types and their default character limits."""
    return [ElementTypeInfo(**et) for et in list_element_types()]

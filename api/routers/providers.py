"""Provider endpoints — list available LLM providers and models."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from runtime.providers import list_providers

router = APIRouter(prefix="/providers", tags=["providers"])


class ProviderResponse(BaseModel):
    """A supported LLM provider."""

    name: str
    label: str
    default_model: str
    models: list[str]
    key_placeholder: str


@router.get("", response_model=list[ProviderResponse])
async def get_providers() -> list[ProviderResponse]:
    """List all supported LLM providers."""
    return [
        ProviderResponse(
            name=p.name,
            label=p.label,
            default_model=p.default_model,
            models=p.models,
            key_placeholder=p.key_placeholder,
        )
        for p in list_providers()
    ]

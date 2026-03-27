"""Auth endpoints — API key management and current user info."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.cloud.api.deps import CurrentUser, get_current_user, get_db, require_role
from packages.cloud.auth import generate_api_key
from packages.cloud.database import APIKeyCRUD

router = APIRouter(prefix="/v2/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class APIKeyCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, description="Human-readable key name")
    scopes: list[str] = Field(default_factory=lambda: ["agent:run", "score:run"])


class APIKeyCreateResponse(BaseModel):
    id: str
    name: str
    key: str = Field(..., description="Full key — shown only at creation time")
    prefix: str
    scopes: list[str]
    created_at: str


class APIKeySummary(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: list[str]
    created_at: str
    last_used_at: str | None = None


class CurrentUserResponse(BaseModel):
    user_id: str
    org_id: str
    role: str
    email: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/api-keys", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: APIKeyCreateRequest,
    user: CurrentUser = Depends(require_role("editor")),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreateResponse:
    """Create a new API key for the current organisation."""
    raw_key, prefix = generate_api_key()

    record = await APIKeyCRUD.create(
        db,
        org_id=user.org_id,
        user_id=user.user_id,
        name=body.name,
        key_hash=raw_key,  # CRUD layer should hash before persisting
        prefix=prefix,
        scopes=body.scopes,
    )
    await db.commit()

    return APIKeyCreateResponse(
        id=str(record.id),
        name=record.name,
        key=raw_key,
        prefix=prefix,
        scopes=body.scopes,
        created_at=str(record.created_at),
    )


@router.get("/api-keys", response_model=list[APIKeySummary])
async def list_api_keys(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[APIKeySummary]:
    """List all API keys for the current organisation (secrets are never returned)."""
    keys = await APIKeyCRUD.list_by_org(db, org_id=user.org_id)
    return [
        APIKeySummary(
            id=str(k.id),
            name=k.name,
            prefix=k.prefix,
            scopes=k.scopes or [],
            created_at=str(k.created_at),
            last_used_at=str(k.last_used_at) if k.last_used_at else None,
        )
        for k in keys
    ]


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    user: CurrentUser = Depends(require_role("editor")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke (delete) an API key."""
    key = await APIKeyCRUD.get(db, key_id=key_id, org_id=user.org_id)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key '{key_id}' not found.",
        )
    await APIKeyCRUD.delete(db, key_id=key_id)
    await db.commit()


@router.get("/me", response_model=CurrentUserResponse)
async def get_current_user_info(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUserResponse:
    """Return information about the currently authenticated user."""
    return CurrentUserResponse(
        user_id=user.user_id,
        org_id=user.org_id,
        role=user.role,
        email=user.email,
    )

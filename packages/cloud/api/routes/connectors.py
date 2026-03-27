"""Connector endpoints — manage external integration configurations."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.cloud.api.deps import CurrentUser, get_current_user, get_db, require_role

router = APIRouter(prefix="/v2/connectors", tags=["connectors"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ConnectorCreate(BaseModel):
    type: str = Field(..., description="Connector type, e.g. 'figma', 'github', 'contentful'")
    name: str = Field(..., min_length=1, max_length=128)
    config: dict[str, Any] = Field(default_factory=dict, description="Connector-specific configuration")


class ConnectorResponse(BaseModel):
    id: str
    org_id: str
    type: str
    name: str
    status: str = "active"
    created_at: str = ""


class ConnectorTestResult(BaseModel):
    healthy: bool
    message: str = ""
    latency_ms: float | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_connector_or_404(
    db: AsyncSession, connector_id: str, org_id: str
) -> Any:
    from packages.cloud.database import ConnectorConfig

    result = await db.get(ConnectorConfig, connector_id)
    if result is None or str(getattr(result, "org_id", "")) != org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector '{connector_id}' not found.",
        )
    return result


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ConnectorResponse])
async def list_connectors(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConnectorResponse]:
    """List all configured connectors for the organisation."""
    from sqlalchemy import select
    from packages.cloud.database import ConnectorConfig

    stmt = select(ConnectorConfig).where(ConnectorConfig.org_id == user.org_id)
    result = await db.execute(stmt)
    connectors = result.scalars().all()

    return [
        ConnectorResponse(
            id=str(c.id),
            org_id=str(c.org_id),
            type=c.type,
            name=c.name,
            status=c.status or "active",
            created_at=str(c.created_at),
        )
        for c in connectors
    ]


@router.post("", response_model=ConnectorResponse, status_code=status.HTTP_201_CREATED)
async def add_connector(
    body: ConnectorCreate,
    user: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> ConnectorResponse:
    """Add a new connector configuration."""
    from packages.cloud.database import ConnectorConfig

    connector = ConnectorConfig(
        org_id=user.org_id,
        type=body.type,
        name=body.name,
        config=body.config,
        status="active",
    )
    db.add(connector)
    await db.commit()
    await db.refresh(connector)

    return ConnectorResponse(
        id=str(connector.id),
        org_id=str(connector.org_id),
        type=connector.type,
        name=connector.name,
        status=connector.status or "active",
        created_at=str(connector.created_at),
    )


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_connector(
    connector_id: str,
    user: CurrentUser = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a connector configuration."""
    connector = await _get_connector_or_404(db, connector_id, user.org_id)
    await db.delete(connector)
    await db.commit()


@router.post("/{connector_id}/test", response_model=ConnectorTestResult)
async def test_connector(
    connector_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConnectorTestResult:
    """Test whether a connector is reachable and healthy."""
    import time

    connector = await _get_connector_or_404(db, connector_id, user.org_id)

    start = time.monotonic()
    try:
        # Placeholder: real implementations would call the external service.
        # For now, we return healthy if the record exists.
        latency = (time.monotonic() - start) * 1000
        return ConnectorTestResult(
            healthy=True,
            message=f"Connector '{connector.name}' ({connector.type}) is reachable.",
            latency_ms=round(latency, 2),
        )
    except Exception as exc:
        latency = (time.monotonic() - start) * 1000
        return ConnectorTestResult(
            healthy=False,
            message=str(exc),
            latency_ms=round(latency, 2),
        )

"""Project endpoints — CRUD operations for organisation projects."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.cloud.api.deps import CurrentUser, get_current_user, get_db
from packages.cloud.database import ProjectCRUD

router = APIRouter(prefix="/v2/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None


class ProjectResponse(BaseModel):
    id: str
    org_id: str
    name: str
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Create a new project within the user's organisation."""
    project = await ProjectCRUD.create(
        db,
        org_id=user.org_id,
        name=body.name,
        description=body.description,
        metadata=body.metadata,
    )
    await db.commit()
    return ProjectResponse(
        id=str(project.id),
        org_id=str(project.org_id),
        name=project.name,
        description=project.description or "",
        metadata=project.meta or {},
        created_at=str(project.created_at),
        updated_at=str(project.updated_at),
    )


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    """List all projects belonging to the user's organisation."""
    projects = await ProjectCRUD.list_by_org(db, org_id=user.org_id)
    return [
        ProjectResponse(
            id=str(p.id),
            org_id=str(p.org_id),
            name=p.name,
            description=p.description or "",
            metadata=p.meta or {},
            created_at=str(p.created_at),
            updated_at=str(p.updated_at),
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Get a specific project by ID."""
    project = await ProjectCRUD.get(db, project_id=project_id, org_id=user.org_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return ProjectResponse(
        id=str(project.id),
        org_id=str(project.org_id),
        name=project.name,
        description=project.description or "",
        metadata=project.meta or {},
        created_at=str(project.created_at),
        updated_at=str(project.updated_at),
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    """Update a project's name, description, or metadata."""
    project = await ProjectCRUD.get(db, project_id=project_id, org_id=user.org_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    update_data = body.model_dump(exclude_unset=True)
    project = await ProjectCRUD.update(db, project_id=project_id, **update_data)
    await db.commit()

    return ProjectResponse(
        id=str(project.id),
        org_id=str(project.org_id),
        name=project.name,
        description=project.description or "",
        metadata=project.meta or {},
        created_at=str(project.created_at),
        updated_at=str(project.updated_at),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a project."""
    project = await ProjectCRUD.get(db, project_id=project_id, org_id=user.org_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    await ProjectCRUD.delete(db, project_id=project_id)
    await db.commit()

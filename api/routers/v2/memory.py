from __future__ import annotations
from fastapi import APIRouter
from api.models_v2 import MemorySearchRequest, MemoryStatsResponse

router = APIRouter(prefix="/api/v2/memory", tags=["memory-v2"])

@router.post("/search")
async def search_memory(request: MemorySearchRequest):
    from runtime.memory_hierarchy import MemoryHierarchy
    hierarchy = MemoryHierarchy()

    results = hierarchy.search(query=request.query, n_results=request.limit)
    entries = []
    for entry in (results or []):
        entries.append({
            "key": getattr(entry, 'key', ''),
            "value": getattr(entry, 'value', str(entry)),
            "category": getattr(entry, 'category', 'general'),
            "source_agent": getattr(entry, 'source_agent', ''),
            "scope": "project",
            "timestamp": str(getattr(entry, 'timestamp', '')),
        })
    return {"results": entries}

@router.get("/stats", response_model=MemoryStatsResponse)
async def memory_stats():
    from runtime.memory_hierarchy import MemoryHierarchy
    hierarchy = MemoryHierarchy()

    session_count = len(hierarchy.session.entries) if hasattr(hierarchy.session, 'entries') else 0
    project_count = len(hierarchy.project.entries) if hasattr(hierarchy.project, 'entries') else 0
    workspace_count = len(hierarchy.workspace.entries) if hasattr(hierarchy.workspace, 'entries') else 0

    return MemoryStatsResponse(
        session_count=session_count,
        project_count=project_count,
        workspace_count=workspace_count,
        total_entries=session_count + project_count + workspace_count,
    )

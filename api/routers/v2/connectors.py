from __future__ import annotations
from fastapi import APIRouter, HTTPException
from api.models_v2 import ConnectorSyncRequest

router = APIRouter(prefix="/api/v2/connectors", tags=["connectors-v2"])

@router.get("")
async def list_connectors():
    try:
        from runtime.connectors.registry import ConnectorRegistry
        registry = ConnectorRegistry()
        connectors = []
        for name, connector in registry.get_all().items():
            connectors.append({
                "name": name,
                "type": getattr(connector, 'connector_type', 'unknown'),
                "status": getattr(connector, 'status', 'disconnected'),
                "last_sync": getattr(connector, 'last_sync', None),
                "entry_count": getattr(connector, 'entry_count', 0),
            })
        return {"connectors": connectors}
    except Exception:
        return {"connectors": []}

@router.post("/{name}/sync")
async def sync_connector(name: str, request: ConnectorSyncRequest):
    from runtime.connectors.registry import ConnectorRegistry
    registry = ConnectorRegistry()
    connector = registry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")
    try:
        result = connector.sync(mode=request.sync_mode, dry_run=request.dry_run)
        return {"sync_result": vars(result) if result else {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{name}/health")
async def connector_health(name: str):
    from runtime.connectors.registry import ConnectorRegistry
    registry = ConnectorRegistry()
    connector = registry.get(name)
    if not connector:
        raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")
    try:
        health = connector.health_check()
        return vars(health) if health else {"status": "unknown"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.delete("/{name}")
async def disconnect_connector(name: str):
    """Disconnect/remove a connector."""
    try:
        from runtime.connectors.registry import ConnectorRegistry
        registry = ConnectorRegistry()
        connector = registry.get(name)
        if not connector:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail=f"Connector '{name}' not found")
        if hasattr(connector, 'disconnect'):
            connector.disconnect()
        elif hasattr(connector, 'close'):
            connector.close()
        return {"status": "disconnected", "name": name}
    except Exception as e:
        if "404" in str(type(e).__name__) or "HTTPException" in str(type(e)):
            raise
        return {"status": "error", "message": str(e)}

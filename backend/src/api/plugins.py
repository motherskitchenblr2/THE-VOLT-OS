"""VOLT OS — Plugin System API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from src.core.database import get_db
from src.core.events import EventBus
from src.plugins.service import PluginService
from src.plugins.models import PluginType, PluginStatus

router = APIRouter(prefix="/api/plugins", tags=["plugins"])

event_bus = EventBus()


class PluginInstallRequest(BaseModel):
    manifest: dict


class PluginUpgradeRequest(BaseModel):
    manifest: dict


class PluginResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str | None
    type: str
    version: str
    api_version: str
    status: str
    capabilities: list
    permissions: list
    health_status: str | None
    last_error: str | None

    class Config:
        from_attributes = True


@router.post("/install", response_model=PluginResponse)
def install_plugin(req: PluginInstallRequest, db: Session = Depends(get_db)):
    svc = PluginService(db, event_bus)
    try:
        plugin = svc.install(req.manifest)
        return plugin
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/activate", response_model=PluginResponse)
def activate_plugin(plugin_id: str, db: Session = Depends(get_db)):
    svc = PluginService(db, event_bus)
    try:
        plugin = svc.activate(plugin_id)
        return plugin
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/deactivate", response_model=PluginResponse)
def deactivate_plugin(plugin_id: str, db: Session = Depends(get_db)):
    svc = PluginService(db, event_bus)
    try:
        plugin = svc.deactivate(plugin_id)
        return plugin
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{plugin_id}/upgrade", response_model=PluginResponse)
def upgrade_plugin(plugin_id: str, req: PluginUpgradeRequest, db: Session = Depends(get_db)):
    svc = PluginService(db, event_bus)
    try:
        plugin = svc.upgrade(plugin_id, req.manifest)
        return plugin
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{plugin_id}")
def remove_plugin(plugin_id: str, db: Session = Depends(get_db)):
    svc = PluginService(db, event_bus)
    try:
        svc.remove(plugin_id)
        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[PluginResponse])
def list_plugins(
    type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    svc = PluginService(db, event_bus)
    type_filter = PluginType(type) if type else None
    status_filter = PluginStatus(status) if status else None
    return svc.list_plugins(type_filter, status_filter)


@router.get("/{plugin_id}", response_model=PluginResponse)
def get_plugin(plugin_id: str, db: Session = Depends(get_db)):
    svc = PluginService(db, event_bus)
    try:
        return svc.get(plugin_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

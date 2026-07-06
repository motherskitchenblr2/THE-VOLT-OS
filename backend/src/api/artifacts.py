"""VOLT OS — Artifact Registry API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.core.database import get_db
from src.orchestration.artifacts import ArtifactRegistry

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])


class StoreArtifactRequest(BaseModel):
    project_id: str
    type: str
    content: dict
    produced_by: str | None = None
    execution_id: str | None = None


@router.post("/store")
def store_artifact(req: StoreArtifactRequest, db: Session = Depends(get_db)):
    registry = ArtifactRegistry(db)
    artifact_id = registry.store(req.project_id, req.type, req.content, req.produced_by, req.execution_id)
    return {"id": artifact_id}


@router.get("/{project_id}")
def list_artifacts(project_id: str, db: Session = Depends(get_db)):
    registry = ArtifactRegistry(db)
    return registry.list_artifacts(project_id)


@router.get("/{project_id}/{artifact_type}")
def get_artifact(project_id: str, artifact_type: str, version: int = None, db: Session = Depends(get_db)):
    registry = ArtifactRegistry(db)
    result = registry.get(project_id, artifact_type, version)
    if not result:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return result


@router.get("/{project_id}/{artifact_type}/history")
def version_history(project_id: str, artifact_type: str, db: Session = Depends(get_db)):
    registry = ArtifactRegistry(db)
    return registry.get_version_history(project_id, artifact_type)


@router.post("/{artifact_id}/reject")
def reject_artifact(artifact_id: str, db: Session = Depends(get_db)):
    registry = ArtifactRegistry(db)
    success = registry.reject(artifact_id)
    if not success:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return {"rejected": True}

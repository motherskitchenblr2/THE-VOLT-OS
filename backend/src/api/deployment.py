"""VOLT OS — Deployment API routes."""
from fastapi import APIRouter
from pydantic import BaseModel
from src.core.deployment import DeploymentManager

router = APIRouter(prefix="/api/deploy", tags=["deployment"])
deploy_manager = DeploymentManager()


class DeployRequest(BaseModel):
    provider: str
    project_path: str = "."
    name: str = "volt-os"


@router.get("/providers")
def list_providers():
    return {"providers": deploy_manager.list_providers()}


@router.post("/deploy")
def deploy(req: DeployRequest):
    result = deploy_manager.deploy(req.provider, req.project_path, {"name": req.name})
    return {
        "success": result.success,
        "url": result.url,
        "provider": result.provider,
        "error": result.error,
    }


@router.post("/teardown/{provider}/{deployment_id}")
def teardown(provider: str, deployment_id: str):
    success = deploy_manager.teardown(provider, deployment_id)
    return {"success": success}

"""VOLT OS — Orchestration API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from src.core.database import get_db
from src.core.events import EventBus
from src.orchestration.engine import PipelineEngine, PipelineStageStatus, GateStatus

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

pipeline_engine = PipelineEngine()


class PipelineResponse(BaseModel):
    id: str
    name: str
    domain: str
    stages: list[dict]
    gates: list[dict]


class ExecuteStageRequest(BaseModel):
    stage_id: str
    artifacts: dict = {}


class ApproveGateRequest(BaseModel):
    gate_id: str
    decision: str  # "approved" or "rejected"
    feedback: str = ""


@router.get("/", response_model=list[dict])
def list_pipelines():
    return [
        {"id": p.id, "name": p.name, "domain": p.domain, "stages": len(p.stages)}
        for p in pipeline_engine.pipelines.values()
    ]


@router.get("/{pipeline_id}")
def get_pipeline(pipeline_id: str):
    try:
        p = pipeline_engine.get_pipeline(pipeline_id)
        return {
            "id": p.id,
            "name": p.name,
            "domain": p.domain,
            "stages": [
                {"id": s.id, "name": s.name, "agent_type": s.agent_type, "status": s.status.value, "depends_on": s.depends_on, "is_gate": s.is_gate}
                for s in p.stages
            ],
            "gates": [
                {"id": g.id, "status": g.status.value, "criteria": g.criteria}
                for g in p.gates
            ],
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{pipeline_id}/ready")
def get_ready_stages(pipeline_id: str):
    try:
        p = pipeline_engine.get_pipeline(pipeline_id)
        ready = pipeline_engine.get_ready_stages(p)
        return [{"id": s.id, "name": s.name, "agent_type": s.agent_type, "input_artifacts": s.input_artifacts} for s in ready]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{pipeline_id}/stages/{stage_id}/complete")
def complete_stage(pipeline_id: str, stage_id: str, req: ExecuteStageRequest):
    try:
        p = pipeline_engine.get_pipeline(pipeline_id)
        stage = next((s for s in p.stages if s.id == stage_id), None)
        if not stage:
            raise HTTPException(status_code=404, detail=f"Stage not found: {stage_id}")
        stage.status = PipelineStageStatus.COMPLETED
        stage.result = req.artifacts
        return {"status": "completed", "stage_id": stage_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{pipeline_id}/gates/{gate_id}/approve")
def approve_gate(pipeline_id: str, gate_id: str, req: ApproveGateRequest):
    try:
        p = pipeline_engine.get_pipeline(pipeline_id)
        gate = next((g for g in p.gates if g.id == gate_id), None)
        if not gate:
            raise HTTPException(status_code=404, detail=f"Gate not found: {gate_id}")

        if req.decision == "approved":
            gate.status = GateStatus.PASSED
        else:
            gate.status = GateStatus.FAILED
        gate.feedback = req.feedback
        return {"status": gate.status.value, "gate_id": gate_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{pipeline_id}/status")
def pipeline_status(pipeline_id: str):
    try:
        p = pipeline_engine.get_pipeline(pipeline_id)
        completed = sum(1 for s in p.stages if s.status == PipelineStageStatus.COMPLETED)
        total = len(p.stages)
        return {
            "pipeline_id": p.id,
            "progress": f"{completed}/{total}",
            "percentage": round(completed / total * 100, 1) if total > 0 else 0,
            "stages": {s.id: s.status.value for s in p.stages},
            "gates": {g.id: g.status.value for g in p.gates},
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

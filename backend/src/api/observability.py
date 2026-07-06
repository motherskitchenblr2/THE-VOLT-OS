"""VOLT OS — Observability API routes. Mission Control data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.core.observability import ObservabilityService

router = APIRouter(prefix="/api/observability", tags=["observability"])


@router.get("/summary/{project_id}")
def mission_control_summary(project_id: str, db: Session = Depends(get_db)):
    svc = ObservabilityService(db)
    return svc.get_mission_control_summary(project_id)


@router.get("/cost/{project_id}")
def cost_breakdown(project_id: str, db: Session = Depends(get_db)):
    svc = ObservabilityService(db)
    return svc.get_cost_breakdown(project_id)


@router.get("/latency/{project_id}")
def latency_stats(project_id: str, db: Session = Depends(get_db)):
    svc = ObservabilityService(db)
    return svc.get_latency_stats(project_id)


@router.get("/health/agents")
def agent_health(db: Session = Depends(get_db)):
    svc = ObservabilityService(db)
    return svc.get_agent_health()


@router.get("/audit")
def audit_log(limit: int = 50, db: Session = Depends(get_db)):
    from src.core.observability import AuditLog
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
    return [
        {"id": l.id, "actor": l.actor, "action": l.action, "resource_type": l.resource_type, "status": l.status, "timestamp": l.timestamp.isoformat() if l.timestamp else None}
        for l in logs
    ]

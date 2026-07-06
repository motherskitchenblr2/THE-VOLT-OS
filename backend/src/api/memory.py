"""VOLT OS — Memory API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from src.core.database import get_db
from src.core.events import EventBus
from src.memory.service import MemoryService
from src.memory.models import MemoryLevel
import redis

router = APIRouter(prefix="/api/memory", tags=["memory"])

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
event_bus = EventBus()


class StoreRequest(BaseModel):
    level: str
    scope_id: str
    key: str
    content: dict
    tags: list[str] = []


class SearchRequest(BaseModel):
    query: str
    level: str
    scope_id: str | None = None
    top_k: int = 5


class DecisionRequest(BaseModel):
    project_id: str
    agent: str
    decision: str
    rationale: str = ""
    alternatives: list[str] = []
    reversible: bool = True
    reversal_cost: str = "low"


@router.post("/store")
def store_memory(req: StoreRequest, db: Session = Depends(get_db)):
    svc = MemoryService(db, redis_client, event_bus)
    entry_id = svc.store(MemoryLevel(req.level), req.scope_id, req.key, req.content, req.tags)
    return {"id": entry_id}


@router.get("/retrieve/{level}/{scope_id}/{key}")
def retrieve_memory(level: str, scope_id: str, key: str, db: Session = Depends(get_db)):
    svc = MemoryService(db, redis_client, event_bus)
    result = svc.retrieve(MemoryLevel(level), scope_id, key)
    if result is None:
        raise HTTPException(status_code=404, detail="Memory not found")
    return result


@router.post("/search")
def search_memory(req: SearchRequest, db: Session = Depends(get_db)):
    svc = MemoryService(db, redis_client, event_bus)
    return svc.search(req.query, MemoryLevel(req.level), req.scope_id, req.top_k)


@router.post("/forget")
def forget_memory(level: str, scope_id: str, key: str, reason: str = "", db: Session = Depends(get_db)):
    svc = MemoryService(db, redis_client, event_bus)
    success = svc.forget(MemoryLevel(level), scope_id, key, reason)
    return {"forgotten": success}


@router.post("/decisions")
def record_decision(req: DecisionRequest, db: Session = Depends(get_db)):
    svc = MemoryService(db, redis_client, event_bus)
    record_id = svc.record_decision(req.project_id, req.agent, req.decision, req.rationale, req.alternatives, req.reversible, req.reversal_cost)
    return {"id": record_id}


@router.get("/decisions/{project_id}")
def get_decisions(project_id: str, db: Session = Depends(get_db)):
    svc = MemoryService(db, redis_client, event_bus)
    return svc.get_decision_history(project_id)

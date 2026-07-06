"""VOLT OS — Observability layer. Metrics, tracing, audit logging."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Float, Integer
from sqlalchemy.sql import func
from src.core.database import Base
import time
import json


class AuditLog(Base):
    """Append-only audit log for every platform action."""
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    actor = Column(String(100), nullable=False)  # user_id or agent_id
    actor_type = Column(String(20), nullable=False)  # "user" or "agent"
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(36))
    details = Column(JSON)
    ip_address = Column(String(45))
    status = Column(String(20), default="success")  # success, failure


class MetricSnapshot(Base):
    """Point-in-time metric snapshots for Mission Control dashboard."""
    __tablename__ = "metric_snapshots"

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    category = Column(String(50), nullable=False)  # cost, latency, tokens, success_rate, security
    metric_name = Column(String(100), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(20))  # usd, ms, tokens, percent
    labels = Column(JSON, default=dict)  # {project_id, agent_type, model, etc.}


class ObservabilityService:
    """Tracks metrics, audit logs, and provides Mission Control data."""

    def __init__(self, db):
        self.db = db

    def audit(self, actor: str, actor_type: str, action: str, resource_type: str = None,
              resource_id: str = None, details: dict = None, status: str = "success"):
        """Record an audit event."""
        log = AuditLog(
            id=f"aud-{int(time.time()*1000)}",
            actor=actor,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            status=status,
        )
        self.db.add(log)
        self.db.commit()

    def record_metric(self, category: str, name: str, value: float, unit: str = None, labels: dict = None):
        """Record a metric snapshot."""
        snapshot = MetricSnapshot(
            id=f"met-{int(time.time()*1000)}",
            category=category,
            metric_name=name,
            value=value,
            unit=unit,
            labels=labels or {},
        )
        self.db.add(snapshot)
        self.db.commit()

    def get_cost_breakdown(self, project_id: str = None) -> dict:
        """Get cost breakdown by model, agent, project."""
        q = self.db.query(MetricSnapshot).filter(MetricSnapshot.category == "cost")
        if project_id:
            q = q.filter(MetricSnapshot.labels["project_id"].astext == project_id)
        snapshots = q.order_by(MetricSnapshot.timestamp.desc()).limit(1000).all()

        breakdown = {"total_usd": 0, "by_model": {}, "by_agent": {}}
        for s in snapshots:
            breakdown["total_usd"] += s.value
            model = s.labels.get("model", "unknown")
            agent = s.labels.get("agent_type", "unknown")
            breakdown["by_model"][model] = breakdown["by_model"].get(model, 0) + s.value
            breakdown["by_agent"][agent] = breakdown["by_agent"].get(agent, 0) + s.value
        return breakdown

    def get_latency_stats(self, project_id: str = None) -> dict:
        """Get latency statistics (p50, p95, p99)."""
        q = self.db.query(MetricSnapshot).filter(MetricSnapshot.category == "latency")
        if project_id:
            q = q.filter(MetricSnapshot.labels["project_id"].astext == project_id)
        snapshots = q.order_by(MetricSnapshot.timestamp.desc()).limit(1000).all()

        values = sorted([s.value for s in snapshots])
        if not values:
            return {"p50": 0, "p95": 0, "p99": 0, "count": 0}

        return {
            "p50": values[len(values) // 2],
            "p95": values[int(len(values) * 0.95)],
            "p99": values[int(len(values) * 0.99)],
            "count": len(values),
        }

    def get_success_rate(self, project_id: str = None) -> dict:
        """Get success/failure rates."""
        q = self.db.query(AuditLog)
        if project_id:
            q = q.filter(AuditLog.resource_id == project_id)
        logs = q.order_by(AuditLog.timestamp.desc()).limit(1000).all()

        total = len(logs)
        success = sum(1 for l in logs if l.status == "success")
        return {
            "total": total,
            "success": success,
            "failure": total - success,
            "rate": round(success / total * 100, 1) if total > 0 else 100.0,
        }

    def get_agent_health(self) -> list[dict]:
        """Get health status of all agents."""
        logs = self.db.query(AuditLog).filter(
            AuditLog.actor_type == "agent"
        ).order_by(AuditLog.timestamp.desc()).limit(200).all()

        agents = {}
        for log in logs:
            agent = log.actor
            if agent not in agents:
                agents[agent] = {"name": agent, "total": 0, "failures": 0, "last_action": None}
            agents[agent]["total"] += 1
            if log.status == "failure":
                agents[agent]["failures"] += 1
            if not agents[agent]["last_action"]:
                agents[agent]["last_action"] = log.action

        for a in agents.values():
            a["health"] = "healthy" if a["failures"] / max(a["total"], 1) < 0.1 else "degraded"

        return list(agents.values())

    def get_mission_control_summary(self, project_id: str = None) -> dict:
        """Full Mission Control summary for a project."""
        return {
            "cost": self.get_cost_breakdown(project_id),
            "latency": self.get_latency_stats(project_id),
            "success_rate": self.get_success_rate(project_id),
            "agents": self.get_agent_health(),
        }

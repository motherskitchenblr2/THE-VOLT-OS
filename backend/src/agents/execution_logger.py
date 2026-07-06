"""VOLT OS — Agent Execution Logger. Tracks every agent run."""
from sqlalchemy.orm import Session
from src.agents.models import AgentExecution, AgentStatus
from src.core.observability import ObservabilityService
import uuid
from datetime import datetime, timezone


class ExecutionLogger:
    """Logs agent executions to database and emits metrics for Mission Control."""

    def __init__(self, db: Session, observability: ObservabilityService):
        self.db = db
        self.obs = observability

    def start(self, project_id: str, task_id: str, agent_type: str, input_artifacts: dict = None) -> str:
        """Log agent execution start."""
        exec_id = str(uuid.uuid4())
        execution = AgentExecution(
            id=exec_id,
            project_id=project_id,
            task_id=task_id,
            agent_type=agent_type,
            input_artifacts=input_artifacts or {},
            status=AgentStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(execution)
        self.db.commit()

        self.obs.audit(
            actor=agent_type,
            actor_type="agent",
            action="execution_started",
            resource_type="agent_execution",
            resource_id=exec_id,
            details={"project_id": project_id, "task_id": task_id},
        )
        return exec_id

    def complete(self, exec_id: str, output_artifacts: dict = None, model_used: str = None,
                 tokens_input: int = 0, tokens_output: int = 0, cost_usd: float = 0.0, duration_ms: int = 0):
        """Log agent execution completion."""
        execution = self.db.query(AgentExecution).filter(AgentExecution.id == exec_id).first()
        if not execution:
            return

        execution.status = AgentStatus.COMPLETED
        execution.output_artifacts = output_artifacts or {}
        execution.model_used = model_used
        execution.tokens_input = tokens_input
        execution.tokens_output = tokens_output
        execution.cost_usd = cost_usd
        execution.duration_ms = duration_ms
        execution.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        # Emit metrics
        self.obs.record_metric("cost", "agent_cost", cost_usd, "usd", {"agent_type": execution.agent_type, "model": model_used or "unknown"})
        self.obs.record_metric("latency", "agent_latency", duration_ms, "ms", {"agent_type": execution.agent_type})
        self.obs.record_metric("tokens", "agent_tokens", tokens_input + tokens_output, "tokens", {"agent_type": execution.agent_type, "model": model_used or "unknown"})

        self.obs.audit(
            actor=execution.agent_type,
            actor_type="agent",
            action="execution_completed",
            resource_type="agent_execution",
            resource_id=exec_id,
            details={"cost_usd": cost_usd, "duration_ms": duration_ms},
        )

    def fail(self, exec_id: str, error: str, duration_ms: int = 0):
        """Log agent execution failure."""
        execution = self.db.query(AgentExecution).filter(AgentExecution.id == exec_id).first()
        if not execution:
            return

        execution.status = AgentStatus.FAILED
        execution.error = error
        execution.duration_ms = duration_ms
        execution.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        self.obs.record_metric("latency", "agent_failure", duration_ms, "ms", {"agent_type": execution.agent_type})
        self.obs.audit(
            actor=execution.agent_type,
            actor_type="agent",
            action="execution_failed",
            resource_type="agent_execution",
            resource_id=exec_id,
            details={"error": error},
            status="failure",
        )

    def get_executions(self, project_id: str, limit: int = 50) -> list[dict]:
        """Get recent executions for a project."""
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.project_id == project_id
        ).order_by(AgentExecution.created_at.desc()).limit(limit).all()

        return [
            {
                "id": e.id,
                "agent_type": e.agent_type,
                "status": e.status.value,
                "model_used": e.model_used,
                "cost_usd": e.cost_usd,
                "duration_ms": e.duration_ms,
                "tokens": (e.tokens_input or 0) + (e.tokens_output or 0),
                "started_at": e.started_at.isoformat() if e.started_at else None,
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
            }
            for e in executions
        ]

    def get_project_stats(self, project_id: str) -> dict:
        """Get aggregated stats for a project."""
        executions = self.db.query(AgentExecution).filter(
            AgentExecution.project_id == project_id
        ).all()

        total = len(executions)
        completed = sum(1 for e in executions if e.status == AgentStatus.COMPLETED)
        failed = sum(1 for e in executions if e.status == AgentStatus.FAILED)
        total_cost = sum(e.cost_usd or 0 for e in executions)
        total_duration = sum(e.duration_ms or 0 for e in executions)
        total_tokens = sum((e.tokens_input or 0) + (e.tokens_output or 0) for e in executions)

        return {
            "total_executions": total,
            "completed": completed,
            "failed": failed,
            "success_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "total_cost_usd": round(total_cost, 4),
            "total_duration_ms": total_duration,
            "total_tokens": total_tokens,
        }

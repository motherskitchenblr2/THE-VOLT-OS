"""VOLT OS — Temporal Worker. Replaces in-memory executor with Temporal workflows."""
from dataclasses import dataclass
from typing import Any
from src.orchestration.engine import PipelineEngine, PipelineStageStatus


class TemporalWorker:
    """Temporal-based workflow executor. Replaces the in-memory PipelineWorkflow.

    In production, this registers Temporal workflows and activities.
    For now, it wraps the existing engine with Temporal-compatible patterns.
    """

    def __init__(self, engine: PipelineEngine):
        self.engine = engine

    async def execute_pipeline(self, pipeline_id: str, project_id: str, project_brief: dict) -> dict:
        """Execute a full pipeline using Temporal-compatible patterns."""
        pipeline = self.engine.get_pipeline(pipeline_id)
        project_artifacts = {"project_brief": project_brief}
        execution_log = []

        while True:
            ready_stages = self.engine.get_ready_stages(pipeline)
            if not ready_stages:
                break

            for stage in ready_stages:
                if stage.is_gate:
                    gate_result = self._handle_gate(pipeline, stage)
                    execution_log.append(gate_result)
                    if gate_result["status"] == "failed":
                        return {"status": "failed", "stage": stage.id, "log": execution_log}
                else:
                    # Execute stage with retry logic (Temporal pattern)
                    result = await self._execute_with_retry(stage, project_id, project_artifacts)
                    execution_log.append(result)

                    if result["status"] == "completed":
                        project_artifacts.update(result.get("output_artifacts", {}))
                        stage.status = PipelineStageStatus.COMPLETED
                        stage.result = result.get("output_artifacts", {})
                    else:
                        stage.status = PipelineStageStatus.FAILED
                        return {"status": "failed", "stage": stage.id, "error": result.get("error"), "log": execution_log}

        return {"status": "completed", "artifacts": project_artifacts, "log": execution_log}

    async def _execute_with_retry(self, stage, project_id: str, artifacts: dict, max_retries: int = 2) -> dict:
        """Execute a stage with exponential backoff retry (Temporal activity pattern)."""
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                result = await self._execute_stage(stage, project_id, artifacts)
                if result["status"] == "completed":
                    return result
                last_error = result.get("error", "Unknown error")
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return {"stage_id": stage.id, "status": "failed", "error": f"Failed after {max_retries + 1} attempts: {last_error}"}

    async def _execute_stage(self, stage, project_id: str, artifacts: dict) -> dict:
        """Execute a single pipeline stage via the appropriate agent."""
        from src.agents.registry import AgentRegistry
        from src.agents.interface import AgentContext
        from src.model_router.router import ModelRouter

        model_router = ModelRouter()
        registry = AgentRegistry(model_router)

        agent = registry.get(stage.agent_type)
        context = AgentContext(
            project_id=project_id,
            task_id=f"{project_id}-{stage.id}",
            agent_type=stage.agent_type,
            input_artifacts={k: artifacts.get(k) for k in stage.input_artifacts if k in artifacts},
            memory={},
            permissions=["artifact.read", "artifact.write", "sandbox.execute"],
        )
        agent.initialize(context)
        result = agent.execute({})
        agent.cleanup()

        return {
            "stage_id": stage.id,
            "status": result.status.value,
            "output_artifacts": result.output_artifacts,
            "error": result.error,
            "tokens_used": result.tokens_used,
            "cost_usd": result.cost_usd,
            "duration_ms": result.duration_ms,
        }

    def _handle_gate(self, pipeline, stage) -> dict:
        """Evaluate an approval gate."""
        gate = next((g for g in pipeline.gates if stage.id in g.stage_ids), None)
        if not gate:
            return {"stage_id": stage.id, "status": "passed", "note": "no gate found"}

        from src.orchestration.engine import GateStatus
        status = self.engine.check_gate(gate, pipeline)
        if status == GateStatus.PASSED:
            stage.status = PipelineStageStatus.COMPLETED
            return {"stage_id": stage.id, "status": "passed"}
        elif status == GateStatus.FAILED:
            return {"stage_id": stage.id, "status": "failed", "reason": "gate criteria not met"}
        else:
            stage.status = PipelineStageStatus.WAITING_APPROVAL
            return {"stage_id": stage.id, "status": "waiting_approval", "gate_id": gate.id}

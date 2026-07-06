"""VOLT OS — Orchestration Engine. Temporal-based pipeline DAG execution."""
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class PipelineStageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"
    SKIPPED = "skipped"


class GateStatus(str, Enum):
    OPEN = "open"
    PASSED = "passed"
    FAILED = "failed"
    WAITING = "waiting"


@dataclass
class PipelineStage:
    """A single stage in the pipeline DAG."""
    id: str
    name: str
    agent_type: str
    input_artifacts: list[str]
    output_artifacts: list[str]
    depends_on: list[str] = field(default_factory=list)
    is_gate: bool = False
    status: PipelineStageStatus = PipelineStageStatus.PENDING
    result: dict = field(default_factory=dict)


@dataclass
class ApprovalGate:
    """An approval checkpoint in the pipeline."""
    id: str
    stage_ids: list[str]  # stages that must complete before this gate
    criteria: dict  # pass/fail criteria
    status: GateStatus = GateStatus.OPEN
    decided_by: str | None = None
    decision: str | None = None  # "approved" or "rejected"
    feedback: str | None = None


@dataclass
class Pipeline:
    """A complete pipeline definition."""
    id: str
    name: str
    domain: str
    stages: list[PipelineStage]
    gates: list[ApprovalGate]
    metadata: dict = field(default_factory=dict)


# Software Engineering Domain Pipeline
SOFTWARE_ENGINEERING_PIPELINE = Pipeline(
    id="se-pipeline-v1",
    name="Software Engineering Pipeline",
    domain="software_engineering",
    stages=[
        PipelineStage(
            id="discovery",
            name="Discovery",
            agent_type="researcher",
            input_artifacts=["project_brief"],
            output_artifacts=["requirements", "feasibility_report"],
        ),
        PipelineStage(
            id="research",
            name="Research",
            agent_type="researcher",
            input_artifacts=["requirements"],
            output_artifacts=["tech_research"],
            depends_on=["discovery"],
        ),
        PipelineStage(
            id="architecture",
            name="Architecture Design",
            agent_type="architect",
            input_artifacts=["requirements", "tech_research", "feasibility_report"],
            output_artifacts=["architecture_spec", "risk_assessment", "tech_selection"],
            depends_on=["research"],
        ),
        PipelineStage(
            id="planning",
            name="Project Planning",
            agent_type="architect",
            input_artifacts=["architecture_spec", "risk_assessment"],
            output_artifacts=["task_breakdown"],
            depends_on=["architecture"],
        ),
        PipelineStage(
            id="pre_dev_gate",
            name="Pre-Development Gate",
            agent_type="system",
            input_artifacts=["requirements", "architecture_spec", "task_breakdown", "risk_assessment", "tech_selection"],
            output_artifacts=[],
            depends_on=["planning"],
            is_gate=True,
        ),
        PipelineStage(
            id="frontend_dev",
            name="Frontend Development",
            agent_type="frontend_dev",
            input_artifacts=["architecture_spec", "task_breakdown"],
            output_artifacts=["code"],
            depends_on=["pre_dev_gate"],
        ),
        PipelineStage(
            id="backend_dev",
            name="Backend Development",
            agent_type="backend_dev",
            input_artifacts=["architecture_spec", "task_breakdown"],
            output_artifacts=["code"],
            depends_on=["pre_dev_gate"],
        ),
        PipelineStage(
            id="testing",
            name="Testing",
            agent_type="qa",
            input_artifacts=["code", "architecture_spec", "requirements"],
            output_artifacts=["test_report"],
            depends_on=["frontend_dev", "backend_dev"],
        ),
        PipelineStage(
            id="security_review",
            name="Security Review",
            agent_type="sentinel",
            input_artifacts=["code", "architecture_spec", "test_report"],
            output_artifacts=["security_report"],
            depends_on=["testing"],
        ),
        PipelineStage(
            id="pre_deploy_gate",
            name="Pre-Deployment Gate",
            agent_type="system",
            input_artifacts=["test_report", "security_report", "code"],
            output_artifacts=[],
            depends_on=["security_review"],
            is_gate=True,
        ),
        PipelineStage(
            id="deployment",
            name="Deployment",
            agent_type="infra",
            input_artifacts=["code", "security_report"],
            output_artifacts=["deploy_status"],
            depends_on=["pre_deploy_gate"],
        ),
    ],
    gates=[
        ApprovalGate(
            id="gate-1",
            stage_ids=["pre_dev_gate"],
            criteria={
                "required_artifacts": ["requirements", "architecture_spec", "task_breakdown", "risk_assessment", "tech_selection"],
                "max_critical_risks": 0,
                "require_approval": True,
            },
        ),
        ApprovalGate(
            id="gate-2",
            stage_ids=["pre_deploy_gate"],
            criteria={
                "min_test_coverage": 70.0,
                "max_critical_test_failures": 0,
                "max_security_risk": "medium",
                "max_critical_findings": 0,
                "build_status": "success",
            },
        ),
    ],
)


class PipelineEngine:
    """Executes pipeline DAGs using Temporal workflows."""

    def __init__(self):
        self.pipelines: dict[str, Pipeline] = {}
        self._register_default_pipelines()

    def _register_default_pipelines(self):
        self.pipelines[SOFTWARE_ENGINEERING_PIPELINE.id] = SOFTWARE_ENGINEERING_PIPELINE

    def get_pipeline(self, pipeline_id: str) -> Pipeline:
        if pipeline_id not in self.pipelines:
            raise ValueError(f"Pipeline not found: {pipeline_id}")
        return self.pipelines[pipeline_id]

    def get_ready_stages(self, pipeline: Pipeline) -> list[PipelineStage]:
        """Get stages whose dependencies are all completed."""
        completed = {s.id for s in pipeline.stages if s.status == PipelineStageStatus.COMPLETED}
        return [
            s for s in pipeline.stages
            if s.status == PipelineStageStatus.PENDING
            and all(dep in completed for dep in s.depends_on)
        ]

    def check_gate(self, gate: ApprovalGate, pipeline: Pipeline) -> GateStatus:
        """Evaluate gate pass/fail criteria against completed stages."""
        criteria = gate.criteria

        # Check required artifacts exist
        required = criteria.get("required_artifacts", [])
        completed_artifacts = set()
        for stage in pipeline.stages:
            if stage.status == PipelineStageStatus.COMPLETED:
                completed_artifacts.update(stage.output_artifacts)

        missing = set(required) - completed_artifacts
        if missing:
            return GateStatus.FAILED

        # Check test coverage
        min_coverage = criteria.get("min_test_coverage")
        if min_coverage is not None:
            test_report = self._get_artifact(pipeline, "test_report")
            if test_report and test_report.get("summary", {}).get("coverage", 0) < min_coverage:
                return GateStatus.FAILED

        # Check critical failures
        max_critical = criteria.get("max_critical_test_failures", 0)
        if max_critical is not None:
            test_report = self._get_artifact(pipeline, "test_report")
            if test_report:
                critical = sum(1 for f in test_report.get("failures", []) if f.get("severity") == "critical")
                if critical > max_critical:
                    return GateStatus.FAILED

        # Check security risk
        max_risk = criteria.get("max_security_risk")
        if max_risk:
            security_report = self._get_artifact(pipeline, "security_report")
            if security_report:
                risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
                if risk_order.get(security_report.get("overall_risk", "critical"), 4) > risk_order.get(max_risk, 0):
                    return GateStatus.FAILED

        # Require explicit approval
        if criteria.get("require_approval") and gate.status != GateStatus.PASSED:
            return GateStatus.WAITING

        return GateStatus.PASSED

    def _get_artifact(self, pipeline: Pipeline, artifact_type: str) -> dict | None:
        """Find the latest artifact of a given type from completed stages."""
        for stage in reversed(pipeline.stages):
            if stage.status == PipelineStageStatus.COMPLETED:
                if artifact_type in stage.output_artifacts:
                    return stage.result.get(artifact_type)
        return None

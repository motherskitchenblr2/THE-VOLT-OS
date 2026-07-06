"""VOLT OS — Architect Agent."""
from src.agents.interface import AgentInterface, AgentContext, AgentResult, AgentStatus
from src.model_router.router import ModelRouter
import time


class ArchitectAgent(AgentInterface):
    """System design, architecture decisions, technology selection, task breakdown."""

    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.context: AgentContext | None = None

    def initialize(self, context: AgentContext) -> None:
        self.context = context

    def execute(self, task: dict) -> AgentResult:
        start = time.time()
        try:
            requirements = self.context.input_artifacts.get("requirements", {})
            tech_research = self.context.input_artifacts.get("tech_research", {})
            feasibility = self.context.input_artifacts.get("feasibility_report", {})

            selection = self.model_router.select(
                task_type="architecture",
                complexity="high",
                agent_preferences=[{"model": "claude-sonnet-4", "reason": "architecture reasoning"}],
            )

            architecture_spec = self._generate_architecture(requirements, tech_research)
            risk_assessment = self._generate_risks(requirements, feasibility)
            tech_selection = self._generate_tech_selection(tech_research)
            task_breakdown = self._generate_task_breakdown(architecture_spec, requirements)

            duration_ms = int((time.time() - start) * 1000)

            return AgentResult(
                status=AgentStatus.COMPLETED,
                output_artifacts={
                    "architecture_spec": architecture_spec,
                    "risk_assessment": risk_assessment,
                    "tech_selection": tech_selection,
                    "task_breakdown": task_breakdown,
                },
                cost_usd=selection.estimated_cost_usd,
                duration_ms=duration_ms,
                metadata={"model": selection.model},
            )
        except Exception as e:
            return AgentResult(status=AgentStatus.FAILED, error=str(e), duration_ms=int((time.time() - start) * 1000))

    def health_check(self) -> dict:
        return {"status": "healthy", "agent": "architect"}

    def cleanup(self) -> None:
        self.context = None

    def output_types(self) -> list[str]:
        return ["architecture_spec", "risk_assessment", "tech_selection", "task_breakdown"]

    def input_types(self) -> list[str]:
        return ["requirements", "tech_research", "feasibility_report"]

    def _generate_architecture(self, requirements: dict, tech_research: dict) -> dict:
        return {
            "overview": "System architecture based on requirements analysis",
            "components": [
                {"name": "frontend", "type": "frontend", "responsibility": "User interface", "technology": "Next.js"},
                {"name": "backend", "type": "service", "responsibility": "API and business logic", "technology": "FastAPI"},
                {"name": "database", "type": "database", "responsibility": "Data persistence", "technology": "PostgreSQL"},
            ],
            "data_model": {},
            "api_contracts": [],
            "deployment": {"target": "docker"},
            "decisions": [],
        }

    def _generate_risks(self, requirements: dict, feasibility: dict) -> dict:
        risks = feasibility.get("risks", [])
        for i, r in enumerate(risks, 1):
            r["id"] = f"RISK-{i:03d}"
            r["category"] = "technical"
            r["severity"] = "medium"
            r["owner"] = "architect"
            r["status"] = "open"
        return {
            "risks": risks,
            "overall_risk_level": "medium",
            "mitigation_strategy": "Iterative development with regular checkpoints",
            "residual_risks": [],
        }

    def _generate_tech_selection(self, tech_research: dict) -> dict:
        selections = []
        for tech in tech_research.get("technologies", []):
            selections.append({
                "category": tech.get("category", "other"),
                "selected": tech["name"],
                "version": "latest",
                "justification": tech.get("pros", ["User preference"])[0] if tech.get("pros") else "User preference",
                "alternatives": [],
                "constraints": [],
            })
        return {"selections": selections, "justification": "Based on research and user preferences", "tradeoffs": [], "known_limitations": []}

    def _generate_task_breakdown(self, architecture: dict, requirements: dict) -> dict:
        tasks = []
        components = architecture.get("components", [])
        for i, comp in enumerate(components, 1):
            tasks.append({
                "id": f"TASK-{i:03d}",
                "title": f"Implement {comp['name']}",
                "description": comp.get("responsibility", ""),
                "agent": "frontend_dev" if comp["type"] == "frontend" else "backend_dev",
                "estimated_hours": 8.0,
                "priority": "high",
                "depends_on": [],
                "artifacts_produced": ["code"],
            })
        return {"tasks": tasks, "dependencies": {}, "total_estimate_hours": len(tasks) * 8, "critical_path": [t["id"] for t in tasks]}

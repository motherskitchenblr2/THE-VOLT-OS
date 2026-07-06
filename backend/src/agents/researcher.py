"""VOLT OS — Researcher Agent. First concrete agent implementation."""
from src.agents.interface import AgentInterface, AgentContext, AgentResult, AgentStatus
from src.model_router.router import ModelRouter
from typing import Any
import time


class ResearcherAgent(AgentInterface):
    """Gathers requirements, conducts tech research, assesses feasibility.

    Pipeline stages: Discovery, Research
    Input: project_brief, context
    Output: requirements, tech_research, feasibility_report
    """

    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self.context: AgentContext | None = None

    def initialize(self, context: AgentContext) -> None:
        self.context = context

    def execute(self, task: dict) -> AgentResult:
        start = time.time()
        try:
            # Get project brief from input artifacts
            project_brief = self.context.input_artifacts.get("project_brief", {})
            if not project_brief:
                return AgentResult(
                    status=AgentStatus.FAILED,
                    error="Missing required input: project_brief",
                )

            # Select model
            selection = self.model_router.select(
                task_type="research",
                complexity="medium",
                agent_preferences=[
                    {"model": "claude-sonnet-4", "reason": "long-context synthesis"},
                    {"model": "gpt-4o", "reason": "broad knowledge"},
                ],
            )

            # Generate artifacts (in production, this calls the LLM)
            requirements = self._generate_requirements(project_brief)
            tech_research = self._generate_tech_research(project_brief)
            feasibility = self._generate_feasibility(project_brief, requirements)

            duration_ms = int((time.time() - start) * 1000)

            return AgentResult(
                status=AgentStatus.COMPLETED,
                output_artifacts={
                    "requirements": requirements,
                    "tech_research": tech_research,
                    "feasibility_report": feasibility,
                },
                tokens_used=0,  # populated by LLM integration
                cost_usd=selection.estimated_cost_usd,
                duration_ms=duration_ms,
                metadata={"model": selection.model, "provider": selection.provider},
            )

        except Exception as e:
            return AgentResult(
                status=AgentStatus.FAILED,
                error=str(e),
                duration_ms=int((time.time() - start) * 1000),
            )

    def health_check(self) -> dict:
        return {"status": "healthy", "agent": "researcher"}

    def cleanup(self) -> None:
        self.context = None

    def output_types(self) -> list[str]:
        return ["requirements", "tech_research", "feasibility_report"]

    def input_types(self) -> list[str]:
        return ["project_brief", "context"]

    # --- Artifact generation (LLM calls in production) ---

    def _generate_requirements(self, brief: dict) -> dict:
        """Generate structured requirements from project brief."""
        goals = brief.get("goals", [])
        functional_reqs = []
        for i, goal in enumerate(goals, 1):
            functional_reqs.append({
                "id": f"FR-{i:03d}",
                "description": goal,
                "priority": "must_have" if i <= 3 else "should_have",
                "acceptance_criteria": [],
            })

        return {
            "functional": functional_reqs,
            "non_functional": [
                {"category": "performance", "description": "Response time under 200ms", "target": "200ms"},
                {"category": "security", "description": "Authentication required for all mutations", "target": "Clerk JWT"},
                {"category": "scalability", "description": "Support 1000 concurrent users", "target": "1000"},
            ],
            "constraints": brief.get("constraints", []),
        }

    def _generate_tech_research(self, brief: dict) -> dict:
        """Research technology options for the project."""
        stack_pref = brief.get("preferred_stack", {})
        technologies = []

        if stack_pref.get("frontend"):
            technologies.append({
                "name": stack_pref["frontend"],
                "category": "framework",
                "maturity": "mature",
                "pros": ["Component-based", "Large ecosystem"],
                "cons": ["Bundle size", "Learning curve"],
                "community_score": 9.0,
                "license": "MIT",
            })

        return {
            "technologies": technologies,
            "recommendation": "Follow user's preferred stack",
            "rationale": "User preferences take priority",
            "alternatives_considered": [],
        }

    def _generate_feasibility(self, brief: dict, requirements: dict) -> dict:
        """Assess project feasibility."""
        req_count = len(requirements.get("functional", []))
        complexity = "low" if req_count <= 3 else "medium" if req_count <= 7 else "high"

        return {
            "overall_feasibility": "feasible",
            "complexity": complexity,
            "estimated_effort": {
                "min_hours": req_count * 4,
                "max_hours": req_count * 8,
                "confidence": "medium",
            },
            "risks": [
                {
                    "risk": "Scope creep from vague requirements",
                    "likelihood": "medium",
                    "impact": "medium",
                    "mitigation": "Clear acceptance criteria per requirement",
                }
            ],
            "recommendation": "Proceed with development",
            "blockers": [],
        }

"""VOLT OS — Model Router. Multi-provider LLM selection and cost control."""
from dataclasses import dataclass, field
from typing import Protocol


class ModelProvider(Protocol):
    """Interface for LLM providers. New providers implement this."""
    name: str
    models: list[str]

    async def complete(self, model: str, messages: list[dict], **kwargs) -> dict:
        """Send completion request. Returns {"content": str, "tokens": int, "cost_usd": float}."""
        ...

    async def health(self) -> bool:
        """Check if provider is reachable."""
        ...


@dataclass
class ModelSelection:
    model: str
    provider: str
    estimated_cost_usd: float
    reason: str


@dataclass
class CostTracker:
    """Tracks token usage and cost per task, project, and org."""
    task_budget_usd: float = 2.0
    project_budget_usd: float = 100.0
    org_daily_budget_usd: float = 1000.0
    task_spent_usd: float = 0.0
    project_spent_usd: float = 0.0
    org_daily_spent_usd: float = 0.0

    def can_afford(self, estimated_usd: float) -> bool:
        return (
            self.task_spent_usd + estimated_usd <= self.task_budget_usd
            and self.project_spent_usd + estimated_usd <= self.project_budget_usd
            and self.org_daily_spent_usd + estimated_usd <= self.org_daily_budget_usd
        )

    def record(self, cost_usd: float):
        self.task_spent_usd += cost_usd
        self.project_spent_usd += cost_usd
        self.org_daily_spent_usd += cost_usd


class ModelRouter:
    """Selects the best model per task based on complexity, cost, and agent preferences."""

    def __init__(self):
        self.providers: dict[str, ModelProvider] = {}
        self.cost_tracker = CostTracker()

    def register_provider(self, provider: ModelProvider):
        self.providers[provider.name] = provider

    def select(
        self,
        task_type: str,
        complexity: str,
        agent_preferences: list[dict] = None,
        context_length: int = 0,
    ) -> ModelSelection:
        """Select the best model for a task."""
        # If agent has preferences, try them first (in order)
        if agent_preferences:
            for pref in agent_preferences:
                model = pref["model"]
                provider_name = self._find_provider(model)
                if provider_name:
                    cost = self._estimate_cost(model, task_type)
                    if self.cost_tracker.can_afford(cost):
                        return ModelSelection(
                            model=model,
                            provider=provider_name,
                            estimated_cost_usd=cost,
                            reason=pref.get("reason", "agent preference"),
                        )

        # Fallback: select by task type and complexity
        return self._fallback_select(task_type, complexity)

    def _find_provider(self, model: str) -> str | None:
        for name, provider in self.providers.items():
            if model in provider.models:
                return name
        return None

    def _estimate_cost(self, model: str, task_type: str) -> float:
        """Estimate cost per task. In production, use real pricing."""
        cost_map = {
            "claude-sonnet-4": 0.05,
            "gpt-4o": 0.04,
            "deepseek-chat": 0.01,
            "deepseek-coder": 0.01,
            "qwen": 0.005,
        }
        return cost_map.get(model, 0.05)

    def _fallback_select(self, task_type: str, complexity: str) -> ModelSelection:
        """Fallback selection based on task type."""
        if complexity == "high":
            return ModelSelection(
                model="claude-sonnet-4",
                provider="anthropic",
                estimated_cost_usd=0.05,
                reason="high complexity, best reasoning",
            )
        elif task_type == "code_generation":
            return ModelSelection(
                model="deepseek-coder",
                provider="deepseek",
                estimated_cost_usd=0.01,
                reason="cost-efficient code generation",
            )
        else:
            return ModelSelection(
                model="gpt-4o",
                provider="openai",
                estimated_cost_usd=0.04,
                reason="general purpose fallback",
            )

"""VOLT OS — Agent Registry. Maps agent types to implementations."""
from src.agents.interface import AgentInterface
from src.agents.researcher import ResearcherAgent
from src.agents.architect import ArchitectAgent
from src.agents.frontend_dev import FrontendDevAgent
from src.agents.backend_dev import BackendDevAgent
from src.agents.qa import QAAgent
from src.agents.memory_manager import MemoryManagerAgent
from src.agents.sentinel import SentinelAgent
from src.model_router.router import ModelRouter


class AgentRegistry:
    """Central registry for all agent types and their implementations."""

    def __init__(self, model_router: ModelRouter):
        self.model_router = model_router
        self._agents: dict[str, type[AgentInterface]] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register("researcher", ResearcherAgent)
        self.register("architect", ArchitectAgent)
        self.register("frontend_dev", FrontendDevAgent)
        self.register("backend_dev", BackendDevAgent)
        self.register("qa", QAAgent)
        self.register("memory_manager", MemoryManagerAgent)
        self.register("sentinel", SentinelAgent)

    def register(self, agent_type: str, agent_class: type[AgentInterface]):
        self._agents[agent_type] = agent_class

    def get(self, agent_type: str) -> AgentInterface:
        agent_class = self._agents.get(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        return agent_class(self.model_router)

    def list_types(self) -> list[str]:
        return list(self._agents.keys())

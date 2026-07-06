"""VOLT OS — Agent Runtime interface. Every agent implements this contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class AgentContext:
    """Runtime context provided to an agent on execution."""
    project_id: str
    task_id: str
    agent_id: str
    input_artifacts: dict[str, Any]
    memory: dict[str, Any]
    permissions: list[str]
    model_override: str | None = None
    cost_budget_usd: float = 2.0


@dataclass
class AgentResult:
    """Result returned by an agent after execution."""
    status: AgentStatus
    output_artifacts: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    duration_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentInterface(ABC):
    """Every agent implements this Python interface.

    Agents are data (YAML manifests), but their execution logic
    is implemented via this interface.
    """

    @abstractmethod
    def initialize(self, context: AgentContext) -> None:
        """Load config, connect to memory, validate permissions."""
        ...

    @abstractmethod
    def execute(self, task: dict) -> AgentResult:
        """Main execution loop. Receives task + input artifacts,
        produces output artifacts."""
        ...

    @abstractmethod
    def health_check(self) -> dict:
        """Return current health status."""
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources, flush memory, close connections."""
        ...

    def can_handle(self, artifact_type: str) -> bool:
        """Check if this agent can produce the given artifact type."""
        return artifact_type in self.output_types()

    @abstractmethod
    def output_types(self) -> list[str]:
        """List of artifact types this agent can produce."""
        ...

    @abstractmethod
    def input_types(self) -> list[str]:
        """List of artifact types this agent requires as input."""
        ...

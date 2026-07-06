"""VOLT OS — Agent database models."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Enum as SAEnum
from sqlalchemy.sql import func
from src.core.database import Base
import enum


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentExecution(Base):
    """Tracks every agent execution — inputs, outputs, cost, duration."""
    __tablename__ = "agent_executions"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False, index=True)
    task_id = Column(String(36), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    agent_id = Column(String(36))  # plugin_id if agent is a plugin

    # Input/Output
    input_artifacts = Column(JSON, default=dict)
    output_artifacts = Column(JSON, default=dict)

    # Status
    status = Column(SAEnum(AgentStatus), nullable=False, default=AgentStatus.IDLE)
    error = Column(Text)

    # Cost tracking
    model_used = Column(String(100))
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    duration_ms = Column(Integer, default=0)

    # Metadata
    metadata_ = Column("metadata", JSON, default=dict)

    # Timestamps
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Artifact(Base):
    """Versioned artifact storage."""
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False, index=True)
    type = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False, default=1)

    # Content
    content = Column(JSON, nullable=False)

    # Provenance
    produced_by = Column(String(50))  # agent_type
    execution_id = Column(String(36))

    # Status
    status = Column(String(20), default="active")  # active, rejected, superseded

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

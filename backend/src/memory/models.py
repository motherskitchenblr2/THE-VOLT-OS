"""VOLT OS — Memory System. 5 layers with Redis, PostgreSQL, pgvector."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Boolean
from sqlalchemy.sql import func
from src.core.database import Base
import enum


class MemoryLevel(str, enum.Enum):
    AGENT = "agent"
    PROJECT = "project"
    USER = "user"
    ORG = "org"
    KNOWLEDGE_BASE = "knowledge_base"


class MemoryEntry(Base):
    """Versioned memory storage across all levels."""
    __tablename__ = "memory_entries"

    id = Column(String(36), primary_key=True)
    level = Column(String(20), nullable=False, index=True)
    scope_id = Column(String(36), nullable=False, index=True)  # agent_id, project_id, user_id, org_id
    key = Column(String(200), nullable=False)
    content = Column(JSON, nullable=False)
    embedding_id = Column(String(36))  # reference to vector in pgvector

    # Metadata
    token_count = Column(Integer, default=0)
    access_count = Column(Integer, default=0)
    tags = Column(JSON, default=list)

    # Retention
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_accessed_at = Column(DateTime(timezone=True))


class DecisionRecord(Base):
    """Append-only decision history."""
    __tablename__ = "decision_history"

    id = Column(String(36), primary_key=True)
    project_id = Column(String(36), nullable=False, index=True)
    agent = Column(String(50), nullable=False)
    decision = Column(Text, nullable=False)
    rationale = Column(Text)
    alternatives_considered = Column(JSON, default=list)
    tradeoffs = Column(Text)
    reversible = Column(Boolean, default=True)
    reversal_cost = Column(String(20))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

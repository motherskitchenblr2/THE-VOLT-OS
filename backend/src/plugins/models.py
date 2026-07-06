"""VOLT OS — Plugin System database models."""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Enum as SAEnum
from sqlalchemy.sql import func
from src.core.database import Base
import enum


class PluginType(str, enum.Enum):
    AGENT = "agent"
    TOOL = "tool"
    MODEL_PROVIDER = "model_provider"
    DEPLOY_TARGET = "deploy_target"
    AUTH_PROVIDER = "auth_provider"
    INTEGRATION = "integration"
    SKILL = "skill"


class PluginStatus(str, enum.Enum):
    INSTALLED = "installed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    UPGRADING = "upgrading"


class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    type = Column(SAEnum(PluginType), nullable=False)
    version = Column(String(20), nullable=False)
    api_version = Column(String(20), nullable=False, default="volt/v1")
    status = Column(SAEnum(PluginStatus), nullable=False, default=PluginStatus.INSTALLED)

    # Plugin manifest (YAML parsed to JSON)
    manifest = Column(JSON, nullable=False)

    # Capabilities & requirements
    capabilities = Column(JSON, default=list)
    permissions = Column(JSON, default=list)
    dependencies = Column(JSON, default=list)

    # Runtime config
    entrypoint = Column(String(500))
    config_schema = Column(JSON)

    # Model preferences (for agent plugins)
    model_preference = Column(JSON, default=list)
    cost_profile = Column(JSON)

    # Health
    health_status = Column(String(20), default="unknown")
    last_error = Column(Text)
    consecutive_failures = Column(JSON, default=0)

    # Timestamps
    installed_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deactivated_at = Column(DateTime(timezone=True))

    # Metadata
    metadata_ = Column("metadata", JSON, default=dict)


class PluginAuditLog(Base):
    __tablename__ = "plugin_audit_log"

    id = Column(String(36), primary_key=True)
    plugin_id = Column(String(36), nullable=False)
    action = Column(String(50), nullable=False)  # install, activate, deactivate, upgrade, remove, error
    details = Column(JSON)
    performed_by = Column(String(100))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

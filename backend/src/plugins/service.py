"""VOLT OS — Plugin System service. Core logic for plugin lifecycle."""
from sqlalchemy.orm import Session
from src.plugins.models import Plugin, PluginAuditLog, PluginType, PluginStatus
from src.core.events import EventBus
import uuid
import json


class PluginService:
    """Manages the full plugin lifecycle: install → activate → deactivate → upgrade → remove."""

    def __init__(self, db: Session, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus

    def install(self, manifest: dict) -> Plugin:
        """Install a plugin from its manifest. Validates schema, checks dependencies."""
        # Validate manifest
        self._validate_manifest(manifest)

        # Check if already installed
        existing = self.db.query(Plugin).filter(Plugin.name == manifest["name"]).first()
        if existing:
            raise ValueError(f"Plugin '{manifest['name']}' already installed (v{existing.version})")

        # Check dependencies
        for dep in manifest.get("dependencies", []):
            dep_plugin = self.db.query(Plugin).filter(Plugin.name == dep["name"]).first()
            if not dep_plugin:
                raise ValueError(f"Missing dependency: {dep['name']}")
            if dep_plugin.version != dep.get("version", dep_plugin.version):
                raise ValueError(f"Dependency version mismatch: {dep['name']}")

        plugin = Plugin(
            id=str(uuid.uuid4()),
            name=manifest["name"],
            display_name=manifest.get("display_name", manifest["name"]),
            description=manifest.get("description", ""),
            type=PluginType(manifest["type"]),
            version=manifest["version"],
            api_version=manifest.get("api_version", "volt/v1"),
            status=PluginStatus.INSTALLED,
            manifest=manifest,
            capabilities=manifest.get("capabilities", []),
            permissions=manifest.get("permissions", []),
            dependencies=manifest.get("dependencies", []),
            entrypoint=manifest.get("entrypoint"),
            config_schema=manifest.get("config_schema"),
            model_preference=manifest.get("model_preference", []),
            cost_profile=manifest.get("cost_profile"),
        )

        self.db.add(plugin)
        self._audit(plugin.id, "install", {"version": plugin.version})
        self.db.commit()
        self.db.refresh(plugin)

        self.event_bus.publish("plugin.installed", {"plugin_id": plugin.id, "name": plugin.name})
        return plugin

    def activate(self, plugin_id: str) -> Plugin:
        """Activate an installed plugin."""
        plugin = self._get(plugin_id)
        if plugin.status not in (PluginStatus.INSTALLED, PluginStatus.INACTIVE):
            raise ValueError(f"Cannot activate plugin in status: {plugin.status}")

        # Check dependencies are active
        for dep_name in plugin.dependencies:
            dep = self.db.query(Plugin).filter(Plugin.name == dep_name).first()
            if not dep or dep.status != PluginStatus.ACTIVE:
                raise ValueError(f"Dependency '{dep_name}' is not active")

        plugin.status = PluginStatus.ACTIVE
        plugin.activated_at = func.now()
        plugin.consecutive_failures = 0

        self._audit(plugin.id, "activate")
        self.db.commit()
        self.db.refresh(plugin)

        self.event_bus.publish("plugin.activated", {"plugin_id": plugin.id})
        return plugin

    def deactivate(self, plugin_id: str) -> Plugin:
        """Deactivate an active plugin."""
        plugin = self._get(plugin_id)
        if plugin.status != PluginStatus.ACTIVE:
            raise ValueError(f"Cannot deactivate plugin in status: {plugin.status}")

        # Check no other active plugins depend on this one
        dependents = self.db.query(Plugin).filter(
            Plugin.dependencies.contains(plugin.name),
            Plugin.status == PluginStatus.ACTIVE
        ).all()
        if dependents:
            names = [d.name for d in dependents]
            raise ValueError(f"Cannot deactivate: {', '.join(names)} depend on this plugin")

        plugin.status = PluginStatus.INACTIVE
        plugin.deactivated_at = func.now()

        self._audit(plugin.id, "deactivate")
        self.db.commit()
        self.db.refresh(plugin)

        self.event_bus.publish("plugin.deactivated", {"plugin_id": plugin.id})
        return plugin

    def upgrade(self, plugin_id: str, new_manifest: dict) -> Plugin:
        """Upgrade a plugin to a new version. Backward-compatible API version required."""
        plugin = self._get(plugin_id)
        self._validate_manifest(new_manifest)

        if new_manifest["api_version"] != plugin.api_version:
            raise ValueError(
                f"Breaking change: API version {new_manifest['api_version']} "
                f"!= current {plugin.api_version}. Manual migration required."
            )

        old_version = plugin.version
        plugin.version = new_manifest["version"]
        plugin.manifest = new_manifest
        plugin.capabilities = new_manifest.get("capabilities", plugin.capabilities)
        plugin.permissions = new_manifest.get("permissions", plugin.permissions)

        self._audit(plugin.id, "upgrade", {"from": old_version, "to": new_manifest["version"]})
        self.db.commit()
        self.db.refresh(plugin)

        self.event_bus.publish("plugin.upgraded", {
            "plugin_id": plugin.id,
            "from": old_version,
            "to": new_manifest["version"]
        })
        return plugin

    def remove(self, plugin_id: str) -> None:
        """Remove a plugin. Must be inactive first."""
        plugin = self._get(plugin_id)
        if plugin.status == PluginStatus.ACTIVE:
            raise ValueError("Deactivate plugin before removing")

        self._audit(plugin.id, "remove")
        plugin_id_val = plugin.id
        self.db.delete(plugin)
        self.db.commit()

        self.event_bus.publish("plugin.removed", {"plugin_id": plugin_id_val})

    def get(self, plugin_id: str) -> Plugin:
        return self._get(plugin_id)

    def list_plugins(self, type_filter: PluginType = None, status_filter: PluginStatus = None) -> list[Plugin]:
        query = self.db.query(Plugin)
        if type_filter:
            query = query.filter(Plugin.type == type_filter)
        if status_filter:
            query = query.filter(Plugin.status == status_filter)
        return query.order_by(Plugin.name).all()

    def record_failure(self, plugin_id: str, error: str) -> Plugin:
        """Record an agent/plugin failure. Auto-deactivates after 3 consecutive failures."""
        plugin = self._get(plugin_id)
        plugin.consecutive_failures = (plugin.consecutive_failures or 0) + 1
        plugin.last_error = error

        if plugin.consecutive_failures >= 3:
            plugin.status = PluginStatus.ERROR
            self._audit(plugin.id, "error", {"failures": plugin.consecutive_failures, "error": error})
            self.event_bus.publish("plugin.error", {"plugin_id": plugin_id, "error": error})
        else:
            self._audit(plugin.id, "failure_recorded", {"failures": plugin.consecutive_failures})

        self.db.commit()
        self.db.refresh(plugin)
        return plugin

    def reset_health(self, plugin_id: str) -> Plugin:
        """Reset failure count after successful execution."""
        plugin = self._get(plugin_id)
        plugin.consecutive_failures = 0
        plugin.last_error = None
        if plugin.status == PluginStatus.ERROR:
            plugin.status = PluginStatus.ACTIVE
        self.db.commit()
        self.db.refresh(plugin)
        return plugin

    # --- Internal ---

    def _get(self, plugin_id: str) -> Plugin:
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            raise ValueError(f"Plugin not found: {plugin_id}")
        return plugin

    def _validate_manifest(self, manifest: dict):
        required = ["name", "type", "version"]
        for field in required:
            if field not in manifest:
                raise ValueError(f"Manifest missing required field: {field}")
        try:
            PluginType(manifest["type"])
        except ValueError:
            raise ValueError(f"Invalid plugin type: {manifest['type']}")

    def _audit(self, plugin_id: str, action: str, details: dict = None):
        log = PluginAuditLog(
            id=str(uuid.uuid4()),
            plugin_id=plugin_id,
            action=action,
            details=details or {},
        )
        self.db.add(log)


# Need this import for func.now()
from sqlalchemy.sql import func

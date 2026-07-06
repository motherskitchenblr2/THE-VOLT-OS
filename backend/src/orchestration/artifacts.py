"""VOLT OS — Artifact Registry service. Versioned artifact storage."""
from sqlalchemy.orm import Session
from src.agents.models import Artifact
import uuid


class ArtifactRegistry:
    """Manages versioned artifact storage and retrieval."""

    def __init__(self, db: Session):
        self.db = db

    def store(self, project_id: str, artifact_type: str, content: dict, produced_by: str = None, execution_id: str = None) -> str:
        """Store a new artifact version."""
        # Get latest version number
        latest = self.db.query(Artifact).filter(
            Artifact.project_id == project_id,
            Artifact.type == artifact_type,
        ).order_by(Artifact.version.desc()).first()

        version = (latest.version + 1) if latest else 1

        # Supersede previous version
        if latest:
            latest.status = "superseded"

        artifact = Artifact(
            id=str(uuid.uuid4()),
            project_id=project_id,
            type=artifact_type,
            version=version,
            content=content,
            produced_by=produced_by,
            execution_id=execution_id,
            status="active",
        )
        self.db.add(artifact)
        self.db.commit()
        return artifact.id

    def get(self, project_id: str, artifact_type: str, version: int = None) -> dict | None:
        """Get an artifact. Latest version if version not specified."""
        q = self.db.query(Artifact).filter(
            Artifact.project_id == project_id,
            Artifact.type == artifact_type,
        )
        if version:
            q = q.filter(Artifact.version == version)
        else:
            q = q.filter(Artifact.status == "active")

        artifact = q.order_by(Artifact.version.desc()).first()
        if not artifact:
            return None

        return {
            "id": artifact.id,
            "type": artifact.type,
            "version": artifact.version,
            "content": artifact.content,
            "status": artifact.status,
            "produced_by": artifact.produced_by,
            "created_at": artifact.created_at.isoformat() if artifact.created_at else None,
        }

    def list_artifacts(self, project_id: str) -> list[dict]:
        """List all active artifacts for a project."""
        artifacts = self.db.query(Artifact).filter(
            Artifact.project_id == project_id,
            Artifact.status == "active",
        ).order_by(Artifact.type).all()

        return [
            {"id": a.id, "type": a.type, "version": a.version, "produced_by": a.produced_by}
            for a in artifacts
        ]

    def get_version_history(self, project_id: str, artifact_type: str) -> list[dict]:
        """Get all versions of an artifact type."""
        artifacts = self.db.query(Artifact).filter(
            Artifact.project_id == project_id,
            Artifact.type == artifact_type,
        ).order_by(Artifact.version).all()

        return [
            {"id": a.id, "version": a.version, "status": a.status, "produced_by": a.produced_by}
            for a in artifacts
        ]

    def reject(self, artifact_id: str) -> bool:
        """Mark an artifact as rejected."""
        artifact = self.db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if artifact:
            artifact.status = "rejected"
            self.db.commit()
            return True
        return False

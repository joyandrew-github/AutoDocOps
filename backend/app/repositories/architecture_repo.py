"""Data access layer for the Architecture Intelligence Engine."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.architecture import (
    ArchitectureModel,
    ArchitectureDiagram,
    ArchitectureSnapshot,
    ArchitectureViolation,
)


class ArchitectureRepository:
    """Data access layer for architecture entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- ArchitectureModel ---

    def create_model(self, **kwargs) -> ArchitectureModel:
        m = ArchitectureModel(**kwargs)
        self.db.add(m)
        self.db.commit()
        self.db.refresh(m)
        return m

    def update_model(self, model: ArchitectureModel, **kwargs) -> ArchitectureModel:
        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_model_by_id(self, model_id: int) -> ArchitectureModel | None:
        return self.db.query(ArchitectureModel).filter(ArchitectureModel.id == model_id).first()

    def get_model_by_type(self, repository_id: int, model_type: str) -> ArchitectureModel | None:
        return (
            self.db.query(ArchitectureModel)
            .filter(ArchitectureModel.repository_id == repository_id, ArchitectureModel.model_type == model_type)
            .first()
        )

    def get_models_by_repository(self, repository_id: int) -> list[ArchitectureModel]:
        return (
            self.db.query(ArchitectureModel)
            .filter(ArchitectureModel.repository_id == repository_id)
            .order_by(ArchitectureModel.model_type)
            .all()
        )

    def get_content_hashes(self, repository_id: int) -> dict[str, int]:
        rows = (
            self.db.query(ArchitectureModel.content_hash, ArchitectureModel.id)
            .filter(ArchitectureModel.repository_id == repository_id, ArchitectureModel.content_hash.isnot(None))
            .all()
        )
        return {row[0]: row[1] for row in rows}

    def delete_model(self, model_id: int) -> None:
        self.db.query(ArchitectureModel).filter(ArchitectureModel.id == model_id).delete()
        self.db.commit()

    # --- ArchitectureDiagram ---

    def create_diagram(self, **kwargs) -> ArchitectureDiagram:
        d = ArchitectureDiagram(**kwargs)
        self.db.add(d)
        self.db.commit()
        self.db.refresh(d)
        return d

    def get_diagrams_by_model(self, model_id: int) -> list[ArchitectureDiagram]:
        return (
            self.db.query(ArchitectureDiagram)
            .filter(ArchitectureDiagram.model_id == model_id)
            .order_by(ArchitectureDiagram.diagram_type)
            .all()
        )

    def get_diagrams_by_repository(self, repository_id: int, diagram_type: str | None = None) -> list[ArchitectureDiagram]:
        q = self.db.query(ArchitectureDiagram).filter(ArchitectureDiagram.repository_id == repository_id)
        if diagram_type:
            q = q.filter(ArchitectureDiagram.diagram_type == diagram_type)
        return q.order_by(ArchitectureDiagram.diagram_type).all()

    def delete_diagrams_by_model(self, model_id: int) -> None:
        self.db.query(ArchitectureDiagram).filter(ArchitectureDiagram.model_id == model_id).delete()
        self.db.commit()

    # --- ArchitectureSnapshot ---

    def create_snapshot(self, repository_id: int) -> ArchitectureSnapshot:
        s = ArchitectureSnapshot(repository_id=repository_id)
        self.db.add(s)
        self.db.commit()
        self.db.refresh(s)
        return s

    def update_snapshot(self, snapshot: ArchitectureSnapshot, **kwargs) -> ArchitectureSnapshot:
        for key, value in kwargs.items():
            if hasattr(snapshot, key):
                setattr(snapshot, key, value)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_latest_snapshot(self, repository_id: int) -> ArchitectureSnapshot | None:
        return (
            self.db.query(ArchitectureSnapshot)
            .filter(ArchitectureSnapshot.repository_id == repository_id)
            .order_by(desc(ArchitectureSnapshot.created_at))
            .first()
        )

    def get_snapshots(self, repository_id: int, limit: int = 20) -> list[ArchitectureSnapshot]:
        return (
            self.db.query(ArchitectureSnapshot)
            .filter(ArchitectureSnapshot.repository_id == repository_id)
            .order_by(desc(ArchitectureSnapshot.created_at))
            .limit(limit)
            .all()
        )

    # --- ArchitectureViolation ---

    def create_violation(self, **kwargs) -> ArchitectureViolation:
        v = ArchitectureViolation(**kwargs)
        self.db.add(v)
        self.db.commit()
        self.db.refresh(v)
        return v

    def bulk_create_violations(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(ArchitectureViolation(**rec))
        self.db.commit()

    def get_violations_by_repository(self, repository_id: int, resolved: bool | None = None) -> list[ArchitectureViolation]:
        q = self.db.query(ArchitectureViolation).filter(ArchitectureViolation.repository_id == repository_id)
        if resolved is not None:
            q = q.filter(ArchitectureViolation.is_resolved == resolved)
        return q.order_by(ArchitectureViolation.severity, ArchitectureViolation.violation_type).all()

    def delete_violations_by_repository(self, repository_id: int) -> int:
        count = self.db.query(ArchitectureViolation).filter(ArchitectureViolation.repository_id == repository_id).delete()
        self.db.commit()
        return count

    def count_violations(self, repository_id: int) -> int:
        return self.db.query(ArchitectureViolation).filter(ArchitectureViolation.repository_id == repository_id).count()

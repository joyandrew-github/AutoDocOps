"""Data access layer for the Intelligent Documentation Engine."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.documentation import (
    Documentation,
    DocumentationVersion,
    DocumentationSection,
    DocumentationJob,
)


class DocumentationRepository:
    """Data access layer for documentation entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- Documentation ---

    def create_documentation(self, **kwargs) -> Documentation:
        doc = Documentation(**kwargs)
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def update_documentation(self, doc: Documentation, **kwargs) -> Documentation:
        for key, value in kwargs.items():
            if hasattr(doc, key):
                setattr(doc, key, value)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_documentation_by_id(self, doc_id: int) -> Documentation | None:
        return self.db.query(Documentation).filter(Documentation.id == doc_id).first()

    def get_documentation_by_slug(self, repository_id: int, slug: str) -> Documentation | None:
        return (
            self.db.query(Documentation)
            .filter(Documentation.repository_id == repository_id, Documentation.slug == slug)
            .first()
        )

    def get_documentations_by_repository(
        self,
        repository_id: int,
        doc_type: str | None = None,
        limit: int = 100,
    ) -> list[Documentation]:
        q = self.db.query(Documentation).filter(Documentation.repository_id == repository_id)
        if doc_type:
            q = q.filter(Documentation.doc_type == doc_type)
        return q.order_by(Documentation.doc_type, Documentation.title).limit(limit).all()

    def get_documentation_by_entity(
        self, repository_id: int, entity_type: str, entity_name: str, file_path: str | None = None,
    ) -> Documentation | None:
        q = self.db.query(Documentation).filter(
            Documentation.repository_id == repository_id,
            Documentation.entity_type == entity_type,
            Documentation.entity_name == entity_name,
        )
        if file_path:
            q = q.filter(Documentation.file_path == file_path)
        return q.first()

    def search_documentations(
        self, repository_id: int, query: str, limit: int = 20,
    ) -> list[Documentation]:
        pattern = f"%{query}%"
        return (
            self.db.query(Documentation)
            .filter(
                Documentation.repository_id == repository_id,
                (Documentation.title.ilike(pattern))
                | (Documentation.summary.ilike(pattern))
                | (Documentation.content.ilike(pattern)),
            )
            .order_by(Documentation.doc_type, Documentation.title)
            .limit(limit)
            .all()
        )

    def delete_documentation(self, doc_id: int) -> None:
        self.db.query(Documentation).filter(Documentation.id == doc_id).delete()
        self.db.commit()

    def delete_documentation_by_entity(
        self, repository_id: int, entity_type: str, entity_name: str, file_path: str,
    ) -> int:
        count = (
            self.db.query(Documentation)
            .filter(
                Documentation.repository_id == repository_id,
                Documentation.entity_type == entity_type,
                Documentation.entity_name == entity_name,
                Documentation.file_path == file_path,
            )
            .delete()
        )
        self.db.commit()
        return count

    def delete_documentation_by_file(self, repository_id: int, file_path: str) -> int:
        count = (
            self.db.query(Documentation)
            .filter(Documentation.repository_id == repository_id, Documentation.file_path == file_path)
            .delete()
        )
        self.db.commit()
        return count

    def count_documentations(self, repository_id: int) -> int:
        return self.db.query(Documentation).filter(Documentation.repository_id == repository_id).count()

    def get_content_hashes(self, repository_id: int) -> dict[str, int]:
        rows = (
            self.db.query(Documentation.content_hash, Documentation.id)
            .filter(Documentation.repository_id == repository_id, Documentation.content_hash.isnot(None))
            .all()
        )
        return {row[0]: row[1] for row in rows}

    # --- DocumentationVersion ---

    def create_version(self, **kwargs) -> DocumentationVersion:
        ver = DocumentationVersion(**kwargs)
        self.db.add(ver)
        self.db.commit()
        self.db.refresh(ver)
        return ver

    def get_versions(self, documentation_id: int) -> list[DocumentationVersion]:
        return (
            self.db.query(DocumentationVersion)
            .filter(DocumentationVersion.documentation_id == documentation_id)
            .order_by(desc(DocumentationVersion.version))
            .all()
        )

    # --- DocumentationSection ---

    def create_section(self, **kwargs) -> DocumentationSection:
        sec = DocumentationSection(**kwargs)
        self.db.add(sec)
        self.db.commit()
        self.db.refresh(sec)
        return sec

    def bulk_create_sections(self, records: list[dict]) -> None:
        for rec in records:
            self.db.add(DocumentationSection(**rec))
        self.db.commit()

    def get_sections(self, documentation_id: int) -> list[DocumentationSection]:
        return (
            self.db.query(DocumentationSection)
            .filter(DocumentationSection.documentation_id == documentation_id)
            .order_by(DocumentationSection.section_order)
            .all()
        )

    def delete_sections(self, documentation_id: int) -> None:
        self.db.query(DocumentationSection).filter(
            DocumentationSection.documentation_id == documentation_id
        ).delete()
        self.db.commit()

    # --- DocumentationJob ---

    def create_job(self, repository_id: int, doc_types: str | None = None) -> DocumentationJob:
        job = DocumentationJob(repository_id=repository_id, doc_types_requested=doc_types)
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def update_job(self, job: DocumentationJob, **kwargs) -> DocumentationJob:
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_latest_job(self, repository_id: int) -> DocumentationJob | None:
        return (
            self.db.query(DocumentationJob)
            .filter(DocumentationJob.repository_id == repository_id)
            .order_by(desc(DocumentationJob.created_at))
            .first()
        )

    def get_jobs(self, repository_id: int, limit: int = 20) -> list[DocumentationJob]:
        return (
            self.db.query(DocumentationJob)
            .filter(DocumentationJob.repository_id == repository_id)
            .order_by(desc(DocumentationJob.created_at))
            .limit(limit)
            .all()
        )

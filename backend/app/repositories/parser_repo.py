from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.parser import (
    ParserRun,
    ASTNode,
    Function,
    Class,
    Method,
    Import,
    Export,
    Variable,
    Comment,
    FileParseStatus,
)


class ParserRepository:
    """Data access layer for parser entities."""

    def __init__(self, db: Session):
        self.db = db

    # --- ParserRun ---

    def create_parser_run(self, repository_id: int) -> ParserRun:
        run = ParserRun(repository_id=repository_id, status="pending")
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_parser_run(self, run: ParserRun, **kwargs) -> ParserRun:
        for key, value in kwargs.items():
            if hasattr(run, key):
                setattr(run, key, value)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_latest_parser_run(self, repository_id: int) -> ParserRun | None:
        return (
            self.db.query(ParserRun)
            .filter(ParserRun.repository_id == repository_id)
            .order_by(desc(ParserRun.created_at))
            .first()
        )

    def get_latest_completed_parser_run(self, repository_id: int) -> ParserRun | None:
        return (
            self.db.query(ParserRun)
            .filter(ParserRun.repository_id == repository_id, ParserRun.status == "completed")
            .order_by(desc(ParserRun.created_at))
            .first()
        )

    def get_file_checksums_by_parser_run(self, parser_run_id: int) -> dict[int, str]:
        """Get a mapping of file_id to checksum for a parser run."""
        rows = (
            self.db.query(FileParseStatus.file_id, FileParseStatus.checksum)
            .filter(FileParseStatus.parser_run_id == parser_run_id, FileParseStatus.status == "parsed")
            .all()
        )
        return {row[0]: row[1] for row in rows if row[1]}

    def create_file_parse_status(
        self,
        parser_run_id: int,
        file_id: int,
        status: str,
        checksum: str | None = None,
        previous_checksum: str | None = None,
        error_message: str | None = None,
        nodes_extracted: int = 0,
        parsed_at = None,
    ) -> FileParseStatus:
        file_status = FileParseStatus(
            parser_run_id=parser_run_id,
            file_id=file_id,
            status=status,
            checksum=checksum,
            previous_checksum=previous_checksum,
            error_message=error_message,
            nodes_extracted=nodes_extracted,
            parsed_at=parsed_at,
        )
        self.db.add(file_status)
        self.db.commit()
        self.db.refresh(file_status)
        return file_status

    def delete_nodes_by_file_and_run(self, file_id: int, parser_run_id: int) -> None:
        """Delete AST nodes for a specific file and parser run (for stale record cleanup)."""
        self.db.query(ASTNode).filter(
            ASTNode.file_id == file_id,
            ASTNode.parser_run_id == parser_run_id,
        ).delete()
        self.db.commit()

    # --- Bulk inserts ---

    def bulk_create_functions(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "function"
            node = Function(**rec)
            self.db.add(node)
        self.db.commit()

    def bulk_create_classes(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "class"
            node = Class(**rec)
            self.db.add(node)
        self.db.commit()

    def bulk_create_methods(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "method"
            node = Method(**rec)
            self.db.add(node)
        self.db.commit()

    def bulk_create_imports(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "import"
            node = Import(**rec)
            self.db.add(node)
        self.db.commit()

    def bulk_create_exports(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "export"
            node = Export(**rec)
            self.db.add(node)
        self.db.commit()

    def bulk_create_variables(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "variable"
            node = Variable(**rec)
            self.db.add(node)
        self.db.commit()

    def bulk_create_comments(self, records: list[dict]) -> None:
        for rec in records:
            rec["node_type"] = "comment"
            node = Comment(**rec)
            self.db.add(node)
        self.db.commit()

    # --- Queries ---

    def get_ast_nodes_by_repository(self, repository_id: int) -> list[ASTNode]:
        return (
            self.db.query(ASTNode)
            .join(ParserRun, ASTNode.parser_run_id == ParserRun.id)
            .filter(ParserRun.repository_id == repository_id)
            .order_by(ASTNode.file_id, ASTNode.start_line)
            .all()
        )

    def get_functions_by_repository(self, repository_id: int) -> list[Function]:
        return (
            self.db.query(Function)
            .join(ParserRun, Function.parser_run_id == ParserRun.id)
            .filter(ParserRun.repository_id == repository_id)
            .order_by(Function.file_id, Function.start_line)
            .all()
        )

    def get_classes_by_repository(self, repository_id: int) -> list[Class]:
        return (
            self.db.query(Class)
            .join(ParserRun, Class.parser_run_id == ParserRun.id)
            .filter(ParserRun.repository_id == repository_id)
            .order_by(Class.file_id, Class.start_line)
            .all()
        )

    def get_imports_by_repository(self, repository_id: int) -> list[Import]:
        return (
            self.db.query(Import)
            .join(ParserRun, Import.parser_run_id == ParserRun.id)
            .filter(ParserRun.repository_id == repository_id)
            .order_by(Import.file_id, Import.start_line)
            .all()
        )

    def get_variables_by_repository(self, repository_id: int) -> list[Variable]:
        return (
            self.db.query(Variable)
            .join(ParserRun, Variable.parser_run_id == ParserRun.id)
            .filter(ParserRun.repository_id == repository_id)
            .order_by(Variable.file_id, Variable.start_line)
            .all()
        )

    def delete_nodes_by_parser_run(self, parser_run_id: int) -> None:
        self.db.query(ASTNode).filter(ASTNode.parser_run_id == parser_run_id).delete()
        self.db.commit()

    def delete_nodes_by_file(self, file_id: int, parser_run_id: int) -> None:
        self.db.query(ASTNode).filter(
            ASTNode.file_id == file_id,
            ASTNode.parser_run_id == parser_run_id,
        ).delete()
        self.db.commit()

    def count_nodes_by_type(self, repository_id: int) -> dict[str, int]:
        """Count AST nodes by type for a repository."""
        from sqlalchemy import func as sa_func
        rows = (
            self.db.query(ASTNode.node_type, sa_func.count(ASTNode.id))
            .join(ParserRun, ASTNode.parser_run_id == ParserRun.id)
            .filter(ParserRun.repository_id == repository_id)
            .group_by(ASTNode.node_type)
            .all()
        )
        return {row[0]: row[1] for row in rows}

import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.engines.parser_engine.parser_router import ParserRouter
from app.engines.parser_engine.base_parser import ParseResult
from app.repositories.parser_repo import ParserRepository
from app.repositories.repository_repo import RepositoryRepository
from app.models.parser import ParserRun, FileParseStatus
from app.models.repository import RepositoryFile
from app.core.logging import get_logger

logger = get_logger(__name__)

MAX_WORKERS = 4
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
PARSER_VERSION = "1.0.0"


@dataclass
class FileParseResult:
    file_id: int
    file_path: str
    language: str
    result: ParseResult
    error: str | None = None
    should_parse: bool = True
    checksum: str | None = None


class ParserService:
    """Orchestrates parsing of repository files using tree-sitter with incremental parsing support."""

    def __init__(self, db: Session):
        self.db = db
        self.parser_repo = ParserRepository(db)
        self.repo_repo = RepositoryRepository(db)
        self.router = ParserRouter()

    def parse_repository(self, repository_id: int, force: bool = False) -> ParserRun:
        """Parse all supported files in a repository with incremental parsing support."""
        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        # Create parser run record
        run = self.parser_repo.create_parser_run(repository_id)
        self.parser_repo.update_parser_run(
            run,
            status="in_progress",
            started_at=datetime.now(timezone.utc),
            parser_version=PARSER_VERSION,
        )

        try:
            # Get all files for this repository
            files = self.repo_repo.get_files_by_repository(repository_id)
            if not files:
                self.parser_repo.update_parser_run(
                    run,
                    status="completed",
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=0.0,
                    total_files_parsed=0,
                    files_parsed=0,
                    files_skipped=0,
                    files_failed=0,
                )
                return run

            # Get previous successful parser run for incremental parsing
            previous_run = None
            previous_file_checksums = {}
            if not force:
                previous_run = self.parser_repo.get_latest_completed_parser_run(repository_id)
                if previous_run:
                    previous_file_checksums = self.parser_repo.get_file_checksums_by_parser_run(previous_run.id)

            # Filter to parseable files and determine which need parsing
            parseable_files = [
                f for f in files
                if f.language and self.router.is_supported(f.language)
                and f.size_bytes <= MAX_FILE_SIZE_BYTES
            ]

            logger.info(
                f"Parsing repository {repository_id}: "
                f"{len(parseable_files)}/{len(files)} files are parseable"
            )

            start_time = time.time()

            # Determine which files need parsing (incremental logic)
            files_to_parse = self._determine_files_to_parse(
                parseable_files, previous_file_checksums, force
            )

            logger.info(
                f"Incremental parsing: {len(files_to_parse)} files to parse, "
                f"{len(parseable_files) - len(files_to_parse)} files to skip"
            )

            # Parse files in parallel
            file_results = self._parse_files_parallel(files_to_parse)

            # Store results and track statistics
            total_nodes = 0
            total_functions = 0
            total_classes = 0
            total_imports = 0
            files_parsed = 0
            files_skipped = 0
            files_failed = 0

            # Process parse results
            for fr in file_results:
                if fr.error:
                    logger.warning(f"Error parsing {fr.file_path}: {fr.error}")
                    files_failed += 1
                    # Record failed parse status
                    self.parser_repo.create_file_parse_status(
                        parser_run_id=run.id,
                        file_id=fr.file_id,
                        status="failed",
                        checksum=fr.checksum,
                        error_message=fr.error,
                    )
                    continue

                if not fr.should_parse:
                    # File was skipped (unchanged)
                    files_skipped += 1
                    # Copy previous parse status or create skipped status
                    self.parser_repo.create_file_parse_status(
                        parser_run_id=run.id,
                        file_id=fr.file_id,
                        status="skipped",
                        checksum=fr.checksum,
                        previous_checksum=previous_file_checksums.get(fr.file_id),
                    )
                    continue

                # File was parsed successfully
                files_parsed += 1
                result = fr.result
                total_nodes += result.total_nodes
                total_functions += len(result.functions)
                total_classes += len(result.classes)
                total_imports += len(result.imports)

                # Remove stale AST records for modified files
                if previous_file_checksums.get(fr.file_id) != fr.checksum:
                    self.parser_repo.delete_nodes_by_file_and_run(fr.file_id, run.id)

                # Store parse result
                self._store_parse_result(fr.file_id, run.id, result)

                # Record successful parse status
                self.parser_repo.create_file_parse_status(
                    parser_run_id=run.id,
                    file_id=fr.file_id,
                    status="parsed",
                    checksum=fr.checksum,
                    previous_checksum=previous_file_checksums.get(fr.file_id),
                    nodes_extracted=result.total_nodes,
                    parsed_at=datetime.now(timezone.utc),
                )

            duration = round(time.time() - start_time, 3)

            self.parser_repo.update_parser_run(
                run,
                status="completed",
                total_files_parsed=files_parsed,
                total_nodes_extracted=total_nodes,
                total_functions=total_functions,
                total_classes=total_classes,
                total_imports=total_imports,
                duration_seconds=duration,
                completed_at=datetime.now(timezone.utc),
                files_parsed=files_parsed,
                files_skipped=files_skipped,
                files_failed=files_failed,
            )

            logger.info(
                f"Parsing completed for repository {repository_id}: "
                f"{files_parsed} parsed, {files_skipped} skipped, {files_failed} failed, "
                f"{total_nodes} nodes, {total_functions} functions, "
                f"{total_classes} classes, {total_imports} imports in {duration}s"
            )

        except Exception as e:
            logger.error(f"Parsing failed for repository {repository_id}: {e}")
            self.parser_repo.update_parser_run(
                run,
                status="failed",
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )

        return run

    def _determine_files_to_parse(
        self, files: list[RepositoryFile], previous_checksums: dict[int, str], force: bool
    ) -> list[RepositoryFile]:
        """Determine which files need parsing based on checksums."""
        files_to_parse = []

        for file in files:
            current_checksum = file.checksum
            previous_checksum = previous_checksums.get(file.id)

            # Parse if:
            # - Force mode is enabled
            # - File has no previous checksum (new file or never parsed)
            # - Checksum has changed (modified file)
            if force or not previous_checksum or current_checksum != previous_checksum:
                files_to_parse.append(file)

        return files_to_parse

    def _parse_files_parallel(self, files: list[RepositoryFile]) -> list[FileParseResult]:
        """Parse multiple files in parallel using ThreadPoolExecutor."""
        results: list[FileParseResult] = []

        def parse_single(file: RepositoryFile) -> FileParseResult:
            try:
                source_code = self._read_file(file.absolute_path)
                if source_code is None:
                    return FileParseResult(
                        file_id=file.id,
                        file_path=file.relative_path,
                        language=file.language,
                        result=ParseResult(),
                        error="Could not read file",
                        should_parse=False,
                        checksum=file.checksum,
                    )

                parser = self.router.get_parser(file.language)
                if not parser:
                    return FileParseResult(
                        file_id=file.id,
                        file_path=file.relative_path,
                        language=file.language,
                        result=ParseResult(),
                        error=f"Unsupported language: {file.language}",
                        should_parse=False,
                        checksum=file.checksum,
                    )

                logger.debug(f"Parsing {file.relative_path} ({file.language})")
                result = parser.parse(source_code)

                return FileParseResult(
                    file_id=file.id,
                    file_path=file.relative_path,
                    language=file.language,
                    result=result,
                    error=result.error,
                    should_parse=True,
                    checksum=file.checksum,
                )
            except Exception as e:
                return FileParseResult(
                    file_id=file.id,
                    file_path=file.relative_path,
                    language=file.language or "unknown",
                    result=ParseResult(),
                    error=str(e),
                    should_parse=False,
                    checksum=file.checksum,
                )

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(parse_single, f): f for f in files}
            for future in as_completed(futures):
                results.append(future.result())

        return results

    def _read_file(self, path: str) -> str | None:
        """Read file content safely."""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception as e:
            logger.warning(f"Cannot read file {path}: {e}")
            return None

    def _store_parse_result(self, file_id: int, parser_run_id: int, result: ParseResult) -> None:
        """Store all parsed nodes to the database."""
        base = {"file_id": file_id, "parser_run_id": parser_run_id}

        if result.functions:
            self.parser_repo.bulk_create_functions([
                {**base, "name": f.name, "start_line": f.start_line, "end_line": f.end_line,
                 "start_column": f.start_column, "end_column": f.end_column,
                 "parameters": f.parameters, "return_type": f.return_type,
                 "decorators": f.decorators, "is_async": f.is_async,
                 "is_generator": f.is_generator, "docstring": f.docstring,
                 "body_start_line": f.body_start_line, "body_end_line": f.body_end_line}
                for f in result.functions
            ])

        if result.classes:
            self.parser_repo.bulk_create_classes([
                {**base, "name": c.name, "start_line": c.start_line, "end_line": c.end_line,
                 "start_column": c.start_column, "end_column": c.end_column,
                 "bases": c.bases, "decorators": c.decorators, "docstring": c.docstring,
                 "is_abstract": c.is_abstract, "interfaces": c.interfaces}
                for c in result.classes
            ])

        if result.methods:
            self.parser_repo.bulk_create_methods([
                {**base, "name": m.name, "start_line": m.start_line, "end_line": m.end_line,
                 "start_column": m.start_column, "end_column": m.end_column,
                 "class_name": m.class_name, "parameters": m.parameters,
                 "return_type": m.return_type, "decorators": m.decorators,
                 "is_async": m.is_async, "is_static": m.is_static,
                 "is_constructor": m.is_constructor, "docstring": m.docstring}
                for m in result.methods
            ])

        if result.imports:
            self.parser_repo.bulk_create_imports([
                {**base, "name": i.name, "start_line": i.start_line, "end_line": i.end_line,
                 "start_column": i.start_column, "end_column": i.end_column,
                 "module": i.module, "alias": i.alias,
                 "is_default": i.is_default, "is_wildcard": i.is_wildcard}
                for i in result.imports
            ])

        if result.exports:
            self.parser_repo.bulk_create_exports([
                {**base, "name": e.name, "start_line": e.start_line, "end_line": e.end_line,
                 "start_column": e.start_column, "end_column": e.end_column,
                 "is_default": e.is_default, "exported_type": e.exported_type}
                for e in result.exports
            ])

        if result.variables:
            self.parser_repo.bulk_create_variables([
                {**base, "name": v.name, "start_line": v.start_line, "end_line": v.end_line,
                 "start_column": v.start_column, "end_column": v.end_column,
                 "var_type": v.var_type, "is_constant": v.is_constant,
                 "scope": v.scope, "initial_value": v.initial_value}
                for v in result.variables
            ])

        if result.comments:
            self.parser_repo.bulk_create_comments([
                {**base, "name": None, "start_line": c.start_line, "end_line": c.end_line,
                 "start_column": c.start_column, "end_column": c.end_column,
                 "text": c.text, "comment_type": c.comment_type,
                 "is_docstring": c.is_docstring}
                for c in result.comments
            ])

    def get_ast_summary(self, repository_id: int) -> dict:
        """Get summary of AST nodes for a repository."""
        run = self.parser_repo.get_latest_parser_run(repository_id)
        counts = self.parser_repo.count_nodes_by_type(repository_id)
        return {
            "parser_run": run,
            "total_functions": counts.get("function", 0),
            "total_classes": counts.get("class", 0),
            "total_methods": counts.get("method", 0),
            "total_imports": counts.get("import", 0),
            "total_exports": counts.get("export", 0),
            "total_variables": counts.get("variable", 0),
            "total_comments": counts.get("comment", 0),
        }

    def get_functions(self, repository_id: int):
        return self.parser_repo.get_functions_by_repository(repository_id)

    def get_classes(self, repository_id: int):
        return self.parser_repo.get_classes_by_repository(repository_id)

    def get_imports(self, repository_id: int):
        return self.parser_repo.get_imports_by_repository(repository_id)

    def get_variables(self, repository_id: int):
        return self.parser_repo.get_variables_by_repository(repository_id)

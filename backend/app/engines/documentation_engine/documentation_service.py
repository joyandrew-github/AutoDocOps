"""DocumentationService — orchestrates incremental documentation generation."""
import hashlib
import os
import re
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.engines.documentation_engine.markdown_generator import MarkdownGenerator
from app.repositories.documentation_repo import DocumentationRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.parser_repo import ParserRepository
from app.repositories.memory_repo import MemoryRepository
from app.models.parser import Function, Class, Method, Import, Variable
from app.core.logging import get_logger

logger = get_logger(__name__)

DOC_TYPES = [
    "master_project_doc",
    "repository_overview",
    "file",
    "class",
    "function",
    "module",
    "changelog",
    "onboarding",
    "dependency",
]

DEFAULT_DOC_TYPES = ["master_project_doc"]


class DocumentationService:
    """Generates and maintains documentation from source code data."""

    def __init__(self, db: Session):
        self.db = db
        self.generator = MarkdownGenerator()
        self.doc_repo = DocumentationRepository(db)
        self.repo_repo = RepositoryRepository(db)
        self.parser_repo = ParserRepository(db)
        self.memory_repo = MemoryRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_documentation(
        self,
        repository_id: int,
        doc_types: list[str] | None = None,
    ) -> dict:
        """Generate documentation for a repository. Defaults to single comprehensive master doc."""
        start = time.time()
        requested = doc_types if doc_types is not None else DEFAULT_DOC_TYPES
        stats = {
            "documents_created": 0,
            "documents_updated": 0,
            "documents_skipped": 0,
            "documents_failed": 0,
            "duration_seconds": 0.0,
            "errors": [],
        }

        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        job = self.doc_repo.create_job(repository_id, ",".join(requested))
        self.doc_repo.update_job(job, status="running", started_at=datetime.now(timezone.utc))

        try:
            # Handle deletions from memory engine first
            self._handle_deletions(repository_id, stats)

            # Master project documentation (Single unified dossier)
            if "master_project_doc" in requested:
                self._generate_master_project_doc(repository_id, repository, stats)

            # Legacy granular doc types (if explicitly requested)
            if "repository_overview" in requested:
                self._generate_repository_overview(repository_id, repository, stats)

            if "file" in requested:
                self._generate_file_docs(repository_id, stats)

            if "class" in requested:
                self._generate_class_docs(repository_id, stats)

            if "function" in requested:
                self._generate_function_docs(repository_id, stats)

            if "module" in requested:
                self._generate_module_docs(repository_id, stats)

            if "changelog" in requested:
                self._generate_changelog(repository_id, repository, stats)

            if "onboarding" in requested:
                self._generate_onboarding(repository_id, repository, stats)

            if "dependency" in requested:
                self._generate_dependency_docs(repository_id, repository, stats)

            duration = round(time.time() - start, 3)
            stats["duration_seconds"] = duration

            total = stats["documents_created"] + stats["documents_updated"] + stats["documents_skipped"]
            self.doc_repo.update_job(job,
                status="completed",
                completed_at=datetime.now(timezone.utc),
                total_documents=total,
                documents_created=stats["documents_created"],
                documents_updated=stats["documents_updated"],
                documents_skipped=stats["documents_skipped"],
                documents_failed=stats["documents_failed"],
                duration_seconds=duration,
            )

            logger.info(
                f"Documentation generation completed for repository {repository_id} in {duration}s: "
                f"+{stats['documents_created']} created, ~{stats['documents_updated']} updated, "
                f"{stats['documents_skipped']} skipped, {stats['documents_failed']} failed"
            )

        except Exception as e:
            logger.error(f"Documentation generation failed for repository {repository_id}: {e}")
            self.doc_repo.update_job(job,
                status="failed",
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )
            stats["errors"].append(str(e))

        return stats

    def get_documentation(self, repository_id: int, doc_type: str | None = None) -> list:
        return self.doc_repo.get_documentations_by_repository(repository_id, doc_type)

    def get_documentation_by_id(self, doc_id: int):
        return self.doc_repo.get_documentation_by_id(doc_id)

    def search_documentation(self, repository_id: int, query: str) -> list:
        return self.doc_repo.search_documentations(repository_id, query)

    def export_documentation(self, doc_id: int, format: str = "markdown") -> str | None:
        doc = self.doc_repo.get_documentation_by_id(doc_id)
        if not doc or not doc.content:
            return None
        if format == "html":
            return self.generator.to_html(doc.content)
        elif format == "pdf":
            return self.generator.to_pdf_ready_markdown(doc.content, doc.title)
        return doc.content

    def export_all(self, repository_id: int, format: str = "markdown") -> list[dict]:
        docs = self.doc_repo.get_documentations_by_repository(repository_id)
        results = []
        for doc in docs:
            if not doc.content:
                continue
            if format == "html":
                content = self.generator.to_html(doc.content)
            elif format == "pdf":
                content = self.generator.to_pdf_ready_markdown(doc.content, doc.title)
            else:
                content = doc.content
            results.append({
                "id": doc.id,
                "title": doc.title,
                "doc_type": doc.doc_type,
                "content": content,
                "format": format,
            })
        return results

    def get_master_documentation(self, repository_id: int):
        """Retrieve the single master project documentation for a repository."""
        return self.doc_repo.get_master_documentation(repository_id)

    def generate_master_documentation(self, repository_id: int) -> dict:
        """Generate or update the single master project documentation for a repository."""
        return self.generate_documentation(repository_id, doc_types=["master_project_doc"])

    def export_master_documentation(self, repository_id: int, format: str = "markdown") -> dict | None:
        """Export the single master documentation in markdown or HTML/PDF-ready format."""
        doc = self.get_master_documentation(repository_id)
        if not doc or not doc.content:
            return None
        if format in ["html", "pdf"]:
            content = self.generator.to_html(doc.content, title=doc.title)
        else:
            content = doc.content
        return {
            "title": doc.title,
            "doc_type": doc.doc_type,
            "filename": f"{self._slugify(doc.title)}.{'html' if format in ['html', 'pdf'] else 'md'}",
            "content": content,
            "format": format,
        }

    # ------------------------------------------------------------------
    # Private — incremental helpers
    # ------------------------------------------------------------------

    def _handle_deletions(self, repository_id: int, stats: dict) -> None:
        try:
            change_sets = self.memory_repo.get_change_sets_by_repository(repository_id, limit=1)
            if not change_sets:
                return
            cs = change_sets[0]
            latest = self.memory_repo.get_latest_snapshot(repository_id)
            if not latest or cs.snapshot_id != latest.id:
                return

            file_changes = self.memory_repo.get_file_changes_by_change_set(cs.id)
            for fc in file_changes:
                if fc.change_type == "deleted":
                    try:
                        self.doc_repo.delete_documentation_by_file(repository_id, fc.file_path)
                    except Exception as e:
                        stats["errors"].append(f"delete docs for file {fc.file_path}: {e}")

            entity_changes = self.memory_repo.get_entity_changes_by_change_set(cs.id)
            for ec in entity_changes:
                if ec.change_type == "deleted":
                    try:
                        self.doc_repo.delete_documentation_by_entity(
                            repository_id, ec.entity_type, ec.entity_name, ec.file_path,
                        )
                    except Exception as e:
                        stats["errors"].append(f"delete docs for entity {ec.entity_name}: {e}")
        except Exception as e:
            stats["errors"].append(f"deletions: {e}")

    def _store_or_update(
        self,
        repository_id: int,
        doc_type: str,
        title: str,
        slug: str,
        content: str,
        summary: str,
        sections: list[dict],
        stats: dict,
        entity_type: str | None = None,
        entity_name: str | None = None,
        file_path: str | None = None,
        language: str | None = None,
    ) -> None:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing = self.doc_repo.get_documentation_by_slug(repository_id, slug)

        if existing:
            if existing.content_hash == content_hash:
                stats["documents_skipped"] += 1
                return
            # Update
            new_version = existing.version + 1
            self.doc_repo.create_version(
                documentation_id=existing.id,
                version=existing.version,
                content=existing.content,
                content_hash=existing.content_hash,
                change_summary="Updated by documentation engine.",
            )
            self.doc_repo.update_documentation(existing,
                content=content,
                summary=summary,
                content_hash=content_hash,
                version=new_version,
                language=language,
            )
            self.doc_repo.delete_sections(existing.id)
            for sec in sections:
                self.doc_repo.create_section(documentation_id=existing.id, **sec)
            stats["documents_updated"] += 1
        else:
            doc = self.doc_repo.create_documentation(
                repository_id=repository_id,
                doc_type=doc_type,
                title=title,
                slug=slug,
                entity_type=entity_type,
                entity_name=entity_name,
                file_path=file_path,
                content=content,
                summary=summary,
                content_hash=content_hash,
                language=language,
            )
            for sec in sections:
                self.doc_repo.create_section(documentation_id=doc.id, **sec)
            stats["documents_created"] += 1

    @staticmethod
    def _slugify(text: str) -> str:
        s = text.lower().strip()
        s = re.sub(r'[^\w\s-]', '', s)
        s = re.sub(r'[\s_]+', '-', s)
        return s[:200]

    # ------------------------------------------------------------------
    # Generators per doc type
    # ------------------------------------------------------------------

    def _get_neo4j_stats(self, repository_id: int) -> dict:
        """Fetch node and relationship counts from Neo4j knowledge graph."""
        try:
            from app.db.neo4j import get_neo4j_client
            client = get_neo4j_client()
            if not client.driver:
                client.connect()
            session = client.get_session()
            try:
                n_res = session.run("MATCH (n) WHERE n.repository_id = $repo_id RETURN count(n) AS cnt", repo_id=repository_id).single()
                r_res = session.run("MATCH (n)-[r]->(m) WHERE n.repository_id = $repo_id AND m.repository_id = $repo_id RETURN count(r) AS cnt", repo_id=repository_id).single()
                return {
                    "nodes_count": n_res["cnt"] if n_res else 0,
                    "relationships_count": r_res["cnt"] if r_res else 0,
                }
            finally:
                session.close()
        except Exception as e:
            logger.debug(f"Could not retrieve Neo4j stats for repository {repository_id}: {e}")
            return {"nodes_count": 0, "relationships_count": 0}

    def _extract_code_intelligence(self, repository, files, funcs, classes) -> tuple[dict, list[dict], list[dict]]:
        """Extract subsystems, discovered routes, and discovered env vars from repository files."""
        subsystems: dict[str, list[dict]] = {
            "controllers": [],
            "routes": [],
            "models": [],
            "middleware": [],
            "config": [],
            "utils": [],
            "root": [],
        }

        for f in files:
            p = (f.relative_path if hasattr(f, "relative_path") else f.get("relative_path", "")).lower()
            fdata = {"file_name": getattr(f, "file_name", ""), "relative_path": getattr(f, "relative_path", "")} if hasattr(f, "relative_path") else f
            if "controller" in p:
                subsystems["controllers"].append(fdata)
            elif "route" in p:
                subsystems["routes"].append(fdata)
            elif "model" in p and not p.endswith(".json"):
                subsystems["models"].append(fdata)
            elif "middleware" in p:
                subsystems["middleware"].append(fdata)
            elif "config" in p:
                subsystems["config"].append(fdata)
            elif "util" in p or "helper" in p:
                subsystems["utils"].append(fdata)
            elif "/" not in p:
                subsystems["root"].append(fdata)

        discovered_routes = []
        discovered_envs = []
        seen_env_names = set()
        seen_route_signatures = set()

        local_path = getattr(repository, "local_path", None)
        if local_path and os.path.exists(local_path):
            try:
                for root, dirs, filenames in os.walk(local_path):
                    if any(ignored in root for ignored in ["node_modules", ".git", "venv", "__pycache__", ".next", "dist", "build"]):
                        continue
                    for fname in filenames:
                        if not fname.endswith((".js", ".ts", ".py", ".json", ".env.example")):
                            continue
                        fpath = os.path.join(root, fname)
                        rel_path = os.path.relpath(fpath, local_path).replace("\\", "/")
                        try:
                            with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                                content = fh.read()

                            # Discover environment variables
                            for m in re.finditer(r"process\.env\.([A-Z0-9_]+)", content):
                                vname = m.group(1)
                                if vname not in seen_env_names:
                                    seen_env_names.add(vname)
                                    discovered_envs.append({"name": vname})

                            for m in re.finditer(r"(?:os\.environ\.get|os\.getenv)\s*\(\s*['\"]([A-Z0-9_]+)['\"]", content):
                                vname = m.group(1)
                                if vname not in seen_env_names:
                                    seen_env_names.add(vname)
                                    discovered_envs.append({"name": vname})

                            # Discover routes
                            for m in re.finditer(
                                r"(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]\s*(?:,\s*([^,\)]+))?",
                                content,
                            ):
                                method = m.group(1).upper()
                                path = m.group(2)
                                raw_handler = (m.group(3) or "").strip()
                                handler = raw_handler.split(",")[-1].strip() if raw_handler else "handler"
                                sig = f"{method}:{path}"
                                if sig not in seen_route_signatures:
                                    seen_route_signatures.add(sig)
                                    discovered_routes.append({
                                        "method": method,
                                        "path": path,
                                        "handler": handler,
                                        "file": rel_path,
                                    })

                            for m in re.finditer(
                                r"@(?:app|router|bp)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]",
                                content,
                            ):
                                method = m.group(1).upper()
                                path = m.group(2)
                                sig = f"{method}:{path}"
                                if sig not in seen_route_signatures:
                                    seen_route_signatures.add(sig)
                                    discovered_routes.append({
                                        "method": method,
                                        "path": path,
                                        "handler": "route_handler",
                                        "file": rel_path,
                                    })
                        except Exception:
                            continue
            except Exception as e:
                logger.warning(f"Error scanning local files for code intelligence: {e}")

        return subsystems, discovered_routes, discovered_envs

    def _generate_master_project_doc(self, repository_id: int, repository, stats: dict) -> None:
        try:
            # Clean up old fragmented/unwanted documents so repository maintains ONE unified master doc
            self.doc_repo.delete_fragmented_docs_by_repository(repository_id)

            langs = self.repo_repo.get_languages_by_repository(repository_id)
            fws = self.repo_repo.get_frameworks_by_repository(repository_id)
            deps = self.repo_repo.get_dependencies_by_repository(repository_id)
            files = self.repo_repo.get_files_by_repository(repository_id)
            funcs = self.parser_repo.get_functions_by_repository(repository_id)
            classes = self.parser_repo.get_classes_by_repository(repository_id)

            graph_stats = self._get_neo4j_stats(repository_id)
            subsystems, routes, env_vars = self._extract_code_intelligence(repository, files, funcs, classes)

            res = self.generator.generate_project_master_doc(
                repo_name=repository.name,
                description=repository.description,
                url=repository.url,
                default_branch=repository.default_branch,
                languages=[{"name": getattr(l, "name", ""), "file_count": getattr(l, "file_count", 0), "percentage": getattr(l, "percentage", 0)} for l in langs],
                frameworks=[{"name": getattr(f, "name", ""), "version": getattr(f, "version", None), "confidence": getattr(f, "confidence", 1.0), "detected_by": getattr(f, "detected_by", "Manifest")} for f in fws],
                dependencies=[{"name": getattr(d, "name", ""), "version": getattr(d, "version", None), "package_manager": getattr(d, "package_manager", "npm"), "source_file": getattr(d, "source_file", None)} for d in deps],
                files=[{"file_name": getattr(f, "file_name", ""), "relative_path": getattr(f, "relative_path", ""), "language": getattr(f, "language", ""), "size_bytes": getattr(f, "size_bytes", 0)} for f in files],
                functions=[{"name": getattr(fn, "name", ""), "parameters": getattr(fn, "parameters", None), "return_type": getattr(fn, "return_type", None), "is_async": getattr(fn, "is_async", False), "docstring": getattr(fn, "docstring", None), "start_line": getattr(fn, "start_line", 1), "end_line": getattr(fn, "end_line", 1), "file_path": getattr(fn, "file_path", "")} for fn in funcs],
                classes=[{"name": getattr(c, "name", ""), "bases": getattr(c, "bases", None), "docstring": getattr(c, "docstring", None), "start_line": getattr(c, "start_line", 1), "end_line": getattr(c, "end_line", 1)} for c in classes],
                subsystems=subsystems,
                routes=routes,
                env_vars=env_vars,
                graph_stats=graph_stats,
            )

            if isinstance(res, tuple) and len(res) == 3:
                content, summary, sections = res
            else:
                content, summary, sections = ("# Master Project Documentation", f"Documentation for {repository.name}", [])

            self._store_or_update(
                repository_id=repository_id,
                doc_type="master_project_doc",
                title=f"{repository.name} — Master Project Documentation",
                slug="master-documentation",
                content=content,
                summary=summary,
                sections=sections,
                stats=stats,
            )
        except Exception as e:
            logger.error(f"Failed to generate master project doc for repo {repository_id}: {e}")
            stats["documents_failed"] += 1
            stats["errors"].append(f"master_project_doc: {e}")

    def _generate_repository_overview(self, repository_id: int, repository, stats: dict) -> None:
        try:
            langs = self.repo_repo.get_languages_by_repository(repository_id)
            fws = self.repo_repo.get_frameworks_by_repository(repository_id)
            deps = self.repo_repo.get_dependencies_by_repository(repository_id)
            files = self.repo_repo.get_files_by_repository(repository_id)
            node_counts = self.parser_repo.count_nodes_by_type(repository_id)

            content, summary, sections = self.generator.generate_repository_overview(
                repo_name=repository.name,
                description=repository.description,
                languages=[{"name": l.name, "file_count": l.file_count, "percentage": l.percentage} for l in langs],
                frameworks=[{"name": f.name, "version": f.version} for f in fws],
                dependencies=[{"name": d.name, "version": d.version, "package_manager": d.package_manager} for d in deps],
                file_count=len(files),
                class_count=node_counts.get("class", 0),
                function_count=node_counts.get("function", 0),
            )
            self._store_or_update(
                repository_id, "repository_overview", f"{repository.name} — Overview",
                self._slugify(f"overview-{repository.name}"), content, summary, sections, stats,
            )
        except Exception as e:
            logger.error(f"Failed to generate repository overview: {e}")
            stats["documents_failed"] += 1
            stats["errors"].append(f"repository_overview: {e}")

    def _generate_file_docs(self, repository_id: int, stats: dict) -> None:
        try:
            files = self.repo_repo.get_files_by_repository(repository_id)
            nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)

            file_nodes: dict[int, list] = {}
            for n in nodes:
                file_nodes.setdefault(n.file_id, []).append(n)

            for rf in files:
                try:
                    fnodes = file_nodes.get(rf.id, [])
                    classes = [{"name": n.name, "bases": getattr(n, "bases", None), "docstring": getattr(n, "docstring", None)} for n in fnodes if isinstance(n, Class)]
                    functions = [{"name": n.name, "parameters": getattr(n, "parameters", None), "return_type": getattr(n, "return_type", None), "docstring": getattr(n, "docstring", None)} for n in fnodes if isinstance(n, Function)]
                    imports = [{"module": getattr(n, "module", None), "name": n.name} for n in fnodes if isinstance(n, Import)]
                    variables = [{"name": n.name, "var_type": getattr(n, "var_type", None), "is_constant": getattr(n, "is_constant", False)} for n in fnodes if isinstance(n, Variable)]

                    if not fnodes:
                        continue

                    content, summary, sections = self.generator.generate_file_documentation(
                        file_path=rf.relative_path, language=rf.language,
                        classes=classes, functions=functions, imports=imports, variables=variables,
                    )
                    self._store_or_update(
                        repository_id, "file", rf.file_name,
                        self._slugify(f"file-{rf.relative_path}"), content, summary, sections, stats,
                        entity_type="file", entity_name=rf.file_name, file_path=rf.relative_path, language=rf.language,
                    )
                except Exception as e:
                    logger.error(f"Failed to generate doc for file {rf.relative_path}: {e}")
                    stats["documents_failed"] += 1
                    stats["errors"].append(f"file {rf.relative_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to generate file docs: {e}")
            stats["errors"].append(f"file_docs: {e}")

    def _generate_class_docs(self, repository_id: int, stats: dict) -> None:
        try:
            classes = self.parser_repo.get_classes_by_repository(repository_id)
            files = self.repo_repo.get_files_by_repository(repository_id)
            file_map = {f.id: f for f in files}
            nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)

            for cls in classes:
                try:
                    rf = file_map.get(cls.file_id)
                    fp = rf.relative_path if rf else None
                    methods = [
                        {"name": n.name, "parameters": getattr(n, "parameters", None), "return_type": getattr(n, "return_type", None), "docstring": getattr(n, "docstring", None)}
                        for n in nodes if isinstance(n, Method) and getattr(n, "class_name", None) == cls.name and n.file_id == cls.file_id
                    ]
                    content, summary, sections = self.generator.generate_class_documentation(
                        class_data={"name": cls.name, "bases": cls.bases, "docstring": cls.docstring},
                        methods=methods, file_path=fp,
                    )
                    self._store_or_update(
                        repository_id, "class", f"Class: {cls.name}",
                        self._slugify(f"class-{cls.name}-{fp or ''}"), content, summary, sections, stats,
                        entity_type="class", entity_name=cls.name, file_path=fp,
                    )
                except Exception as e:
                    logger.error(f"Failed to generate doc for class {cls.name}: {e}")
                    stats["documents_failed"] += 1
                    stats["errors"].append(f"class {cls.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to generate class docs: {e}")
            stats["errors"].append(f"class_docs: {e}")

    def _generate_function_docs(self, repository_id: int, stats: dict) -> None:
        try:
            functions = self.parser_repo.get_functions_by_repository(repository_id)
            files = self.repo_repo.get_files_by_repository(repository_id)
            file_map = {f.id: f for f in files}

            for fn in functions:
                try:
                    rf = file_map.get(fn.file_id)
                    fp = rf.relative_path if rf else None
                    content, summary, sections = self.generator.generate_function_documentation(
                        func_data={"name": fn.name, "parameters": fn.parameters, "return_type": fn.return_type, "docstring": fn.docstring, "decorators": fn.decorators},
                        file_path=fp,
                    )
                    self._store_or_update(
                        repository_id, "function", f"Function: {fn.name}",
                        self._slugify(f"function-{fn.name}-{fp or ''}"), content, summary, sections, stats,
                        entity_type="function", entity_name=fn.name, file_path=fp,
                    )
                except Exception as e:
                    logger.error(f"Failed to generate doc for function {fn.name}: {e}")
                    stats["documents_failed"] += 1
                    stats["errors"].append(f"function {fn.name}: {e}")
        except Exception as e:
            logger.error(f"Failed to generate function docs: {e}")
            stats["errors"].append(f"function_docs: {e}")

    def _generate_module_docs(self, repository_id: int, stats: dict) -> None:
        try:
            files = self.repo_repo.get_files_by_repository(repository_id)
            nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)

            # Group files by directory
            dir_files: dict[str, list] = {}
            for rf in files:
                parts = rf.relative_path.rsplit("/", 1)
                directory = parts[0] if len(parts) > 1 else "."
                dir_files.setdefault(directory, []).append(rf)

            file_id_map = {f.id: f for f in files}
            file_nodes: dict[int, list] = {}
            for n in nodes:
                file_nodes.setdefault(n.file_id, []).append(n)

            for dir_path, dir_file_list in dir_files.items():
                try:
                    all_classes = []
                    all_functions = []
                    for rf in dir_file_list:
                        fnodes = file_nodes.get(rf.id, [])
                        for n in fnodes:
                            if isinstance(n, Class):
                                all_classes.append({"name": n.name, "bases": getattr(n, "bases", None)})
                            elif isinstance(n, Function):
                                all_functions.append({"name": n.name, "parameters": getattr(n, "parameters", None), "return_type": getattr(n, "return_type", None)})

                    content, summary, sections = self.generator.generate_module_documentation(
                        module_path=dir_path,
                        files=[{"file_name": f.file_name, "language": f.language} for f in dir_file_list],
                        classes=all_classes,
                        functions=all_functions,
                    )
                    self._store_or_update(
                        repository_id, "module", f"Module: {dir_path}",
                        self._slugify(f"module-{dir_path}"), content, summary, sections, stats,
                        entity_type="module", entity_name=dir_path,
                    )
                except Exception as e:
                    logger.error(f"Failed to generate doc for module {dir_path}: {e}")
                    stats["documents_failed"] += 1
                    stats["errors"].append(f"module {dir_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to generate module docs: {e}")
            stats["errors"].append(f"module_docs: {e}")

    def _generate_changelog(self, repository_id: int, repository, stats: dict) -> None:
        try:
            commits = self.memory_repo.get_commits_by_repository(repository_id, limit=50)
            commit_data = [
                {"commit_hash": c.commit_hash, "author_name": c.author_name, "committed_at": str(c.committed_at or ""), "message": c.message or ""}
                for c in commits
            ]
            content, summary, sections = self.generator.generate_changelog(repository.name, commit_data)
            self._store_or_update(
                repository_id, "changelog", f"Changelog — {repository.name}",
                self._slugify(f"changelog-{repository.name}"), content, summary, sections, stats,
            )
        except Exception as e:
            logger.error(f"Failed to generate changelog: {e}")
            stats["documents_failed"] += 1
            stats["errors"].append(f"changelog: {e}")

    def _generate_onboarding(self, repository_id: int, repository, stats: dict) -> None:
        try:
            langs = self.repo_repo.get_languages_by_repository(repository_id)
            fws = self.repo_repo.get_frameworks_by_repository(repository_id)
            files = self.repo_repo.get_files_by_repository(repository_id)

            content, summary, sections = self.generator.generate_onboarding_guide(
                repo_name=repository.name,
                description=repository.description,
                languages=[{"name": l.name} for l in langs],
                frameworks=[{"name": f.name} for f in fws],
                key_files=[{"relative_path": f.relative_path, "file_name": f.file_name} for f in files[:20]],
            )
            self._store_or_update(
                repository_id, "onboarding", f"Developer Onboarding — {repository.name}",
                self._slugify(f"onboarding-{repository.name}"), content, summary, sections, stats,
            )
        except Exception as e:
            logger.error(f"Failed to generate onboarding: {e}")
            stats["documents_failed"] += 1
            stats["errors"].append(f"onboarding: {e}")

    def _generate_dependency_docs(self, repository_id: int, repository, stats: dict) -> None:
        try:
            deps = self.repo_repo.get_dependencies_by_repository(repository_id)
            if not deps:
                return
            parts = [f"# Dependencies — {repository.name}\n"]
            parts.append("## All Dependencies\n")
            parts.append("| Name | Version | Package Manager | Source |\n|------|---------|----------------|--------|\n")
            for d in deps:
                parts.append(f"| {d.name} | {d.version or 'N/A'} | {d.package_manager} | `{d.source_file or 'N/A'}` |\n")

            content = "\n".join(parts)
            summary = f"Dependency documentation for {repository.name} with {len(deps)} dependencies."
            sections = [{"title": "All Dependencies", "content": content, "section_order": 0, "section_type": "dependencies", "level": 2}]

            self._store_or_update(
                repository_id, "dependency", f"Dependencies — {repository.name}",
                self._slugify(f"dependencies-{repository.name}"), content, summary, sections, stats,
            )
        except Exception as e:
            logger.error(f"Failed to generate dependency docs: {e}")
            stats["documents_failed"] += 1
            stats["errors"].append(f"dependency: {e}")

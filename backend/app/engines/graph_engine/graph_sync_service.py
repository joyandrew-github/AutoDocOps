"""GraphSyncService — synchronizes PostgreSQL entities into Neo4j."""
import time
from pathlib import PurePosixPath
from sqlalchemy.orm import Session
from app.db.neo4j import Neo4jClient
from app.engines.graph_engine.cypher_builder import NodeBuilder, RelationshipBuilder, CypherQuery
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.parser_repo import ParserRepository
from app.repositories.memory_repo import MemoryRepository
from app.models.parser import ASTNode, Function, Class, Method, Import, Export, Variable
from app.core.logging import get_logger

logger = get_logger(__name__)

NODE = NodeBuilder
REL = RelationshipBuilder


class GraphSyncService:
    """Reads PostgreSQL data and synchronizes it into Neo4j."""

    def __init__(self, db: Session, neo4j_client: Neo4jClient):
        self.db = db
        self.neo4j = neo4j_client
        self.repo_repo = RepositoryRepository(db)
        self.parser_repo = ParserRepository(db)
        self.memory_repo = MemoryRepository(db)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def sync_repository(self, repository_id: int) -> dict:
        """Full incremental sync of a repository into Neo4j.

        Returns statistics about the sync operation.
        """
        start = time.time()
        stats = {
            "nodes_created": 0,
            "nodes_updated": 0,
            "nodes_deleted": 0,
            "relationships_created": 0,
            "relationships_removed": 0,
            "errors": [],
        }

        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        repo_uid = f"repo:{repository_id}"
        logger.info(f"Starting graph sync for repository {repository_id}")

        # 1. Sync repository node
        self._sync_repository_node(repository, repo_uid, stats)

        # 2. Sync commit & snapshot nodes (from memory engine)
        self._sync_commits(repository_id, repo_uid, stats)
        self._sync_snapshots(repository_id, repo_uid, stats)

        # 3. Sync files and directories
        self._sync_files_and_directories(repository_id, repo_uid, stats)

        # 4. Sync parsed entities (functions, classes, methods, etc.)
        self._sync_parsed_entities(repository_id, repo_uid, stats)

        # 5. Sync dependencies and frameworks
        self._sync_dependencies(repository_id, repo_uid, stats)
        self._sync_frameworks(repository_id, repo_uid, stats)

        # 6. Sync programming languages
        self._sync_languages(repository_id, repo_uid, stats)

        # 7. Handle deleted entities from memory engine
        self._handle_deletions(repository_id, repo_uid, stats)

        duration = round(time.time() - start, 3)
        stats["duration_seconds"] = duration

        logger.info(
            f"Graph sync completed for repository {repository_id} in {duration}s: "
            f"+{stats['nodes_created']} nodes, ~{stats['nodes_updated']} updated, "
            f"-{stats['nodes_deleted']} deleted, "
            f"+{stats['relationships_created']} rels, -{stats['relationships_removed']} rels"
        )
        return stats

    # ------------------------------------------------------------------
    # Private sync methods
    # ------------------------------------------------------------------

    def _sync_repository_node(self, repository, repo_uid: str, stats: dict) -> None:
        try:
            cq = NODE.merge_node("Repository", "uid", repo_uid, {
                "name": repository.name,
                "url": repository.url,
                "local_path": repository.local_path,
                "default_branch": repository.default_branch,
                "description": repository.description or "",
            })
            self._run(cq)
            stats["nodes_created"] += 1
        except Exception as e:
            logger.error(f"Failed to sync repository node: {e}")
            stats["errors"].append(f"repository: {e}")

    def _sync_commits(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        try:
            commits = self.memory_repo.get_commits_by_repository(repository_id, limit=500)
        except Exception as e:
            logger.error(f"Failed to fetch commits: {e}")
            stats["errors"].append(f"commits: {e}")
            return
        if not commits:
            return
        records = []
        rels = []
        for c in commits:
            commit_uid = f"commit:{repository_id}:{c.commit_hash}"
            records.append({
                "uid": commit_uid,
                "hash": c.commit_hash,
                "author_name": c.author_name or "",
                "author_email": c.author_email or "",
                "message": (c.message or "")[:500],
                "branch": c.branch or "",
                "committed_at": str(c.committed_at) if c.committed_at else "",
            })
            rels.append({"from_val": repo_uid, "to_val": commit_uid})

        try:
            cq = NODE.batch_merge_nodes("Commit", "uid", records)
            result = self._run(cq)
            stats["nodes_created"] += self._count(result)

            cq = REL.batch_merge_relationships("Repository", "uid", "Commit", "uid", "HAS_COMMIT", rels)
            result = self._run(cq)
            stats["relationships_created"] += self._count(result)
        except Exception as e:
            logger.error(f"Failed to sync commits: {e}")
            stats["errors"].append(f"commits: {e}")

    def _sync_snapshots(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        snapshots = self.memory_repo.get_snapshots_by_repository(repository_id, limit=100)
        if not snapshots:
            return
        records = []
        commit_rels = []
        for s in snapshots:
            snap_uid = f"snapshot:{repository_id}:{s.id}"
            records.append({
                "uid": snap_uid,
                "commit_hash": s.commit_hash or "",
                "total_files": s.total_files,
                "total_classes": s.total_classes,
                "total_functions": s.total_functions,
                "snapshot_at": str(s.snapshot_at),
            })
            if s.commit_hash:
                commit_uid = f"commit:{repository_id}:{s.commit_hash}"
                commit_rels.append({"from_val": commit_uid, "to_val": snap_uid})
        try:
            cq = NODE.batch_merge_nodes("Snapshot", "uid", records)
            result = self._run(cq)
            stats["nodes_created"] += self._count(result)

            if commit_rels:
                cq = REL.batch_merge_relationships("Commit", "uid", "Snapshot", "uid", "CREATED", commit_rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)
        except Exception as e:
            logger.error(f"Failed to sync snapshots: {e}")
            stats["errors"].append(f"snapshots: {e}")

    def _sync_files_and_directories(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        files = self.repo_repo.get_files_by_repository(repository_id)
        if not files:
            return

        dir_set: set[str] = set()
        file_records = []
        file_rels = []
        dir_rels = []
        snapshot_file_rels = []

        # Get latest snapshot uid
        latest_snap = self.memory_repo.get_latest_snapshot(repository_id)
        snap_uid = f"snapshot:{repository_id}:{latest_snap.id}" if latest_snap else None

        for f in files:
            file_uid = f"file:{repository_id}:{f.relative_path}"
            file_records.append({
                "uid": file_uid,
                "name": f.file_name,
                "path": f.relative_path,
                "extension": f.extension or "",
                "language": f.language or "",
                "size_bytes": f.size_bytes,
                "checksum": f.sha256_checksum or "",
            })

            # Extract directory hierarchy
            path = PurePosixPath(f.relative_path)
            parent = str(path.parent) if str(path.parent) != "." else ""
            if parent:
                dir_uid = f"dir:{repository_id}:{parent}"
                file_rels.append({"from_val": dir_uid, "to_val": file_uid})
                # Collect all ancestor directories
                parts = PurePosixPath(parent)
                current = str(parts)
                while current and current != ".":
                    dir_set.add(current)
                    current = str(PurePosixPath(current).parent)
                    if current == ".":
                        break
            else:
                file_rels.append({"from_val": repo_uid, "to_val": file_uid})

            if snap_uid:
                snapshot_file_rels.append({"from_val": snap_uid, "to_val": file_uid})

        # Create directory nodes
        dir_records = []
        repo_dir_rels = []
        dir_dir_rels = []
        for d in dir_set:
            dir_uid = f"dir:{repository_id}:{d}"
            dir_records.append({"uid": dir_uid, "path": d, "name": PurePosixPath(d).name})
            parent_dir = str(PurePosixPath(d).parent)
            if parent_dir and parent_dir != ".":
                parent_uid = f"dir:{repository_id}:{parent_dir}"
                dir_dir_rels.append({"from_val": parent_uid, "to_val": dir_uid})
            else:
                repo_dir_rels.append({"from_val": repo_uid, "to_val": dir_uid})

        try:
            if dir_records:
                cq = NODE.batch_merge_nodes("Directory", "uid", dir_records)
                result = self._run(cq)
                stats["nodes_created"] += self._count(result)

            cq = NODE.batch_merge_nodes("File", "uid", file_records)
            result = self._run(cq)
            stats["nodes_created"] += self._count(result)

            # Repository -> Directory
            if repo_dir_rels:
                cq = REL.batch_merge_relationships("Repository", "uid", "Directory", "uid", "CONTAINS", repo_dir_rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)

            # Directory -> Directory
            if dir_dir_rels:
                cq = REL.batch_merge_relationships("Directory", "uid", "Directory", "uid", "CONTAINS", dir_dir_rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)

            # Directory/Repository -> File
            if file_rels:
                # Split into dir->file and repo->file
                dir_file_rels = [r for r in file_rels if r["from_val"].startswith("dir:")]
                repo_file_rels = [r for r in file_rels if r["from_val"].startswith("repo:")]
                if dir_file_rels:
                    cq = REL.batch_merge_relationships("Directory", "uid", "File", "uid", "CONTAINS", dir_file_rels)
                    result = self._run(cq)
                    stats["relationships_created"] += self._count(result)
                if repo_file_rels:
                    cq = REL.batch_merge_relationships("Repository", "uid", "File", "uid", "CONTAINS", repo_file_rels)
                    result = self._run(cq)
                    stats["relationships_created"] += self._count(result)

            # Snapshot -> File
            if snapshot_file_rels and snap_uid:
                cq = REL.batch_merge_relationships("Snapshot", "uid", "File", "uid", "CONTAINS", snapshot_file_rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)

        except Exception as e:
            logger.error(f"Failed to sync files/directories: {e}")
            stats["errors"].append(f"files: {e}")

    def _sync_parsed_entities(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        files = self.repo_repo.get_files_by_repository(repository_id)
        file_map = {f.id: f for f in files}

        nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)
        if not nodes:
            return

        class_records, func_records, method_records = [], [], []
        var_records, import_records, export_records = [], [], []
        interface_records, enum_records = [], []

        file_defines_rels = []
        class_method_rels = []
        var_belongs_rels = []
        class_extends_rels = []
        class_implements_rels = []
        file_imports_rels = []

        for node in nodes:
            rf = file_map.get(node.file_id)
            if not rf:
                continue
            file_uid = f"file:{repository_id}:{rf.relative_path}"
            entity_uid = f"entity:{repository_id}:{node.node_type}:{node.id}"

            base_props = {
                "uid": entity_uid,
                "name": node.name or "",
                "file_path": rf.relative_path,
                "start_line": node.start_line or 0,
                "end_line": node.end_line or 0,
            }

            try:
                if isinstance(node, Function):
                    base_props.update({
                        "parameters": node.parameters or "",
                        "return_type": node.return_type or "",
                        "is_async": node.is_async,
                        "docstring": (node.docstring or "")[:500],
                    })
                    func_records.append(base_props)
                    file_defines_rels.append({"from_val": file_uid, "to_val": entity_uid})

                elif isinstance(node, Class):
                    base_props.update({
                        "bases": node.bases or "",
                        "is_abstract": node.is_abstract,
                        "docstring": (node.docstring or "")[:500],
                    })
                    # Detect interfaces vs enums vs classes
                    if node.bases and "interface" in (node.bases or "").lower():
                        interface_records.append(base_props)
                    else:
                        class_records.append(base_props)
                    file_defines_rels.append({"from_val": file_uid, "to_val": entity_uid})

                    # EXTENDS relationships
                    if node.bases:
                        for base in node.bases.split(","):
                            base = base.strip()
                            if base:
                                class_extends_rels.append({
                                    "child_uid": entity_uid,
                                    "base_name": base,
                                })

                    # IMPLEMENTS relationships
                    if node.interfaces:
                        for iface in node.interfaces.split(","):
                            iface = iface.strip()
                            if iface:
                                class_implements_rels.append({
                                    "class_uid": entity_uid,
                                    "interface_name": iface,
                                })

                elif isinstance(node, Method):
                    base_props.update({
                        "class_name": node.class_name or "",
                        "parameters": node.parameters or "",
                        "return_type": node.return_type or "",
                        "is_async": node.is_async,
                        "is_static": node.is_static,
                        "is_constructor": node.is_constructor,
                    })
                    method_records.append(base_props)
                    file_defines_rels.append({"from_val": file_uid, "to_val": entity_uid})

                    # HAS_METHOD from class
                    if node.class_name:
                        class_method_rels.append({
                            "class_name": node.class_name,
                            "method_uid": entity_uid,
                            "file_uid": file_uid,
                        })

                elif isinstance(node, Import):
                    base_props.update({
                        "module": node.module or "",
                        "alias": node.alias or "",
                        "is_default": node.is_default,
                    })
                    import_records.append(base_props)
                    file_defines_rels.append({"from_val": file_uid, "to_val": entity_uid})

                    # File IMPORTS relationship
                    if node.module:
                        file_imports_rels.append({
                            "file_uid": file_uid,
                            "import_uid": entity_uid,
                        })

                elif isinstance(node, Export):
                    base_props.update({
                        "is_default": node.is_default,
                        "exported_type": node.exported_type or "",
                    })
                    export_records.append(base_props)
                    file_defines_rels.append({"from_val": file_uid, "to_val": entity_uid})

                elif isinstance(node, Variable):
                    base_props.update({
                        "var_type": node.var_type or "",
                        "is_constant": node.is_constant,
                        "scope": node.scope or "",
                    })
                    var_records.append(base_props)
                    file_defines_rels.append({"from_val": file_uid, "to_val": entity_uid})

            except Exception as e:
                logger.error(f"Failed to prepare entity {node.id}: {e}")
                stats["errors"].append(f"entity:{node.id}: {e}")

        # Batch write all entity types
        entity_batches = [
            ("Class", class_records),
            ("Function", func_records),
            ("Method", method_records),
            ("Variable", var_records),
            ("Import", import_records),
            ("Export", export_records),
            ("Interface", interface_records),
            ("Enum", enum_records),
        ]

        for label, records in entity_batches:
            if records:
                try:
                    cq = NODE.batch_merge_nodes(label, "uid", records)
                    result = self._run(cq)
                    stats["nodes_created"] += self._count(result)
                except Exception as e:
                    logger.error(f"Failed to sync {label} nodes: {e}")
                    stats["errors"].append(f"{label}: {e}")

        # File DEFINES relationships
        if file_defines_rels:
            # Group by target label
            all_target_uids = {r["to_val"] for r in file_defines_rels}
            for label, records in entity_batches:
                label_uids = {r["uid"] for r in records}
                label_rels = [r for r in file_defines_rels if r["to_val"] in label_uids]
                if label_rels:
                    try:
                        cq = REL.batch_merge_relationships("File", "uid", label, "uid", "DEFINES", label_rels)
                        result = self._run(cq)
                        stats["relationships_created"] += self._count(result)
                    except Exception as e:
                        logger.error(f"Failed to create DEFINES rels for {label}: {e}")
                        stats["errors"].append(f"DEFINES->{label}: {e}")

        # Class HAS_METHOD
        if class_method_rels:
            try:
                for rel in class_method_rels:
                    # Find the class uid by matching class_name and file
                    for cr in class_records:
                        if cr["name"] == rel["class_name"] and cr["file_path"] == file_map.get(
                            next((n.file_id for n in nodes if f"entity:{repository_id}:{n.node_type}:{n.id}" == rel["method_uid"]), None),
                            type("", (), {"relative_path": ""})()
                        ).relative_path:
                            cq = REL.merge_relationship("Class", "uid", cr["uid"], "Method", "uid", rel["method_uid"], "HAS_METHOD")
                            self._run(cq)
                            stats["relationships_created"] += 1
                            break
            except Exception as e:
                logger.error(f"Failed to create HAS_METHOD rels: {e}")
                stats["errors"].append(f"HAS_METHOD: {e}")

        # File IMPORTS
        if file_imports_rels:
            try:
                rels = [{"from_val": r["file_uid"], "to_val": r["import_uid"]} for r in file_imports_rels]
                cq = REL.batch_merge_relationships("File", "uid", "Import", "uid", "IMPORTS", rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)
            except Exception as e:
                logger.error(f"Failed to create IMPORTS rels: {e}")
                stats["errors"].append(f"IMPORTS: {e}")

    def _sync_dependencies(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        deps = self.repo_repo.get_dependencies_by_repository(repository_id)
        if not deps:
            return
        records = []
        rels = []
        for d in deps:
            dep_uid = f"dep:{repository_id}:{d.package_manager}:{d.name}"
            records.append({
                "uid": dep_uid,
                "name": d.name,
                "version": d.version or "",
                "package_manager": d.package_manager,
                "source_file": d.source_file or "",
            })
            rels.append({"from_val": repo_uid, "to_val": dep_uid})

            # Also link File -> Dependency if source_file is known
            if d.source_file:
                file_uid = f"file:{repository_id}:{d.source_file}"
                rels.append({"from_val": file_uid, "to_val": dep_uid})

        try:
            cq = NODE.batch_merge_nodes("Dependency", "uid", records)
            result = self._run(cq)
            stats["nodes_created"] += self._count(result)

            # Repo DEPENDS_ON
            repo_dep_rels = [r for r in rels if r["from_val"] == repo_uid]
            if repo_dep_rels:
                cq = REL.batch_merge_relationships("Repository", "uid", "Dependency", "uid", "DEPENDS_ON", repo_dep_rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)

            # File DEPENDS_ON
            file_dep_rels = [r for r in rels if r["from_val"] != repo_uid]
            if file_dep_rels:
                cq = REL.batch_merge_relationships("File", "uid", "Dependency", "uid", "DEPENDS_ON", file_dep_rels)
                result = self._run(cq)
                stats["relationships_created"] += self._count(result)
        except Exception as e:
            logger.error(f"Failed to sync dependencies: {e}")
            stats["errors"].append(f"dependencies: {e}")

    def _sync_frameworks(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        frameworks = self.repo_repo.get_frameworks_by_repository(repository_id)
        if not frameworks:
            return
        records = []
        rels = []
        for fw in frameworks:
            fw_uid = f"fw:{repository_id}:{fw.name}"
            records.append({
                "uid": fw_uid,
                "name": fw.name,
                "version": fw.version or "",
                "confidence": fw.confidence,
            })
            rels.append({"from_val": repo_uid, "to_val": fw_uid})
        try:
            cq = NODE.batch_merge_nodes("Framework", "uid", records)
            result = self._run(cq)
            stats["nodes_created"] += self._count(result)

            cq = REL.batch_merge_relationships("Repository", "uid", "Framework", "uid", "USES", rels)
            result = self._run(cq)
            stats["relationships_created"] += self._count(result)
        except Exception as e:
            logger.error(f"Failed to sync frameworks: {e}")
            stats["errors"].append(f"frameworks: {e}")

    def _sync_languages(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        langs = self.repo_repo.get_languages_by_repository(repository_id)
        if not langs:
            return
        records = []
        rels = []
        for lang in langs:
            lang_uid = f"lang:{repository_id}:{lang.name}"
            records.append({
                "uid": lang_uid,
                "name": lang.name,
                "file_count": lang.file_count,
                "percentage": lang.percentage,
            })
            rels.append({"from_val": repo_uid, "to_val": lang_uid})
        try:
            cq = NODE.batch_merge_nodes("ProgrammingLanguage", "uid", records)
            result = self._run(cq)
            stats["nodes_created"] += self._count(result)

            cq = REL.batch_merge_relationships("Repository", "uid", "ProgrammingLanguage", "uid", "USES_LANGUAGE", rels)
            result = self._run(cq)
            stats["relationships_created"] += self._count(result)
        except Exception as e:
            logger.error(f"Failed to sync languages: {e}")
            stats["errors"].append(f"languages: {e}")

    def _handle_deletions(self, repository_id: int, repo_uid: str, stats: dict) -> None:
        """Handle deletions using the Memory Engine change sets."""
        latest_snapshot = self.memory_repo.get_latest_snapshot(repository_id)
        if not latest_snapshot:
            return

        change_sets = self.memory_repo.get_change_sets_by_repository(repository_id, limit=1)
        if not change_sets:
            return

        cs = change_sets[0]
        if cs.snapshot_id != latest_snapshot.id:
            return

        file_changes = self.memory_repo.get_file_changes_by_change_set(cs.id)
        entity_changes = self.memory_repo.get_entity_changes_by_change_set(cs.id)

        # Delete removed files
        for fc in file_changes:
            if fc.change_type == "deleted":
                file_uid = f"file:{repository_id}:{fc.file_path}"
                try:
                    cq = NODE.delete_node("File", "uid", file_uid)
                    self._run(cq)
                    stats["nodes_deleted"] += 1
                except Exception as e:
                    logger.error(f"Failed to delete file node {fc.file_path}: {e}")
                    stats["errors"].append(f"delete file {fc.file_path}: {e}")

        # Delete removed entities
        for ec in entity_changes:
            if ec.change_type == "deleted":
                # We can't know the exact entity uid, so match by name+file
                try:
                    query = (
                        f"MATCH (n {{"
                        f"name: $name, file_path: $file_path"
                        f"}}) WHERE n.uid STARTS WITH $prefix "
                        f"DETACH DELETE n"
                    )
                    params = {
                        "name": ec.entity_name,
                        "file_path": ec.file_path,
                        "prefix": f"entity:{repository_id}:",
                    }
                    self._run(CypherQuery(query=query, params=params))
                    stats["nodes_deleted"] += 1
                except Exception as e:
                    logger.error(f"Failed to delete entity {ec.entity_name}: {e}")
                    stats["errors"].append(f"delete entity {ec.entity_name}: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run(self, cq: CypherQuery):
        """Execute a CypherQuery against Neo4j."""
        with self.neo4j.get_session() as session:
            return session.run(cq.query, **cq.params)

    @staticmethod
    def _count(result) -> int:
        """Extract count from a Neo4j result."""
        try:
            record = result.single()
            if record and "count" in record:
                return record["count"]
            return 1
        except Exception:
            return 1

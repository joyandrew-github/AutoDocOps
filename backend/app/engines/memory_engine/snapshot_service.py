import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.engines.memory_engine.diff_engine import DiffEngine, SnapshotData
from app.engines.memory_engine.commit_tracker import CommitTracker
from app.repositories.memory_repo import MemoryRepository
from app.repositories.repository_repo import RepositoryRepository
from app.repositories.parser_repo import ParserRepository
from app.models.parser import ASTNode, Function, Class, Method, Import, Export, Variable
from app.models.memory import RepositorySnapshot
from app.core.logging import get_logger

logger = get_logger(__name__)


class SnapshotService:
    """Creates repository snapshots and detects changes between them."""

    def __init__(self, db: Session):
        self.db = db
        self.memory_repo = MemoryRepository(db)
        self.repo_repo = RepositoryRepository(db)
        self.parser_repo = ParserRepository(db)
        self.diff_engine = DiffEngine()
        self.commit_tracker = CommitTracker(db)

    def create_snapshot(self, repository_id: int, parser_run_id: int | None = None) -> RepositorySnapshot:
        """Create a snapshot of the current repository state."""
        start_time = time.time()
        repository = self.repo_repo.get_repository_by_id(repository_id)
        if not repository:
            raise ValueError(f"Repository not found: {repository_id}")

        logger.info(f"Creating snapshot for repository {repository_id}")

        # Sync commits from Git
        commit_hash = self.commit_tracker.get_current_commit_hash(repository.local_path)
        if commit_hash:
            self.commit_tracker.sync_commits(repository_id, repository.local_path, repository.default_branch)

        # Get commit from DB
        commit = None
        if commit_hash:
            commit = self.memory_repo.get_commit_by_hash(repository_id, commit_hash)

        # Get parser run and counts
        if not parser_run_id:
            latest_run = self.parser_repo.get_latest_parser_run(repository_id)
            if latest_run:
                parser_run_id = latest_run.id

        counts = self.parser_repo.count_nodes_by_type(repository_id) if parser_run_id else {}
        files = self.repo_repo.get_files_by_repository(repository_id)

        # Create snapshot
        snapshot = self.memory_repo.create_snapshot(
            repository_id=repository_id,
            commit_id=commit.id if commit else None,
            parser_run_id=parser_run_id,
            commit_hash=commit_hash,
            total_files=len(files),
            total_classes=counts.get("class", 0),
            total_functions=counts.get("function", 0),
            total_methods=counts.get("method", 0),
            total_imports=counts.get("import", 0),
            total_variables=counts.get("variable", 0),
            snapshot_at=datetime.now(timezone.utc),
        )

        # Build current snapshot data and create entity versions
        current_data = self._build_snapshot_data(repository_id, files)

        # Get previous snapshot for comparison
        previous_snapshot = self.memory_repo.get_previous_snapshot(repository_id, snapshot.id)

        if previous_snapshot:
            # Build previous snapshot data
            prev_files = self.repo_repo.get_files_by_repository(repository_id)
            previous_data = self._build_snapshot_data_from_versions(previous_snapshot.id)

            # Run diff
            diff_result = self.diff_engine.compare(previous_data, current_data)

            # Store change set
            change_set = self.memory_repo.create_change_set(
                repository_id=repository_id,
                snapshot_id=snapshot.id,
                previous_snapshot_id=previous_snapshot.id,
                commit_hash=commit_hash,
                total_file_changes=len(diff_result.file_diffs),
                total_entity_changes=len(diff_result.entity_diffs),
                files_added=diff_result.files_added,
                files_modified=diff_result.files_modified,
                files_deleted=diff_result.files_deleted,
                files_renamed=diff_result.files_renamed,
                entities_added=diff_result.entities_added,
                entities_modified=diff_result.entities_modified,
                entities_deleted=diff_result.entities_deleted,
            )

            # Store file changes
            if diff_result.file_diffs:
                self.memory_repo.bulk_create_file_changes([
                    {
                        "change_set_id": change_set.id,
                        "file_path": fd.file_path,
                        "previous_path": fd.previous_path,
                        "change_type": fd.change_type,
                        "language": fd.language,
                        "previous_checksum": fd.previous_checksum,
                        "current_checksum": fd.current_checksum,
                    }
                    for fd in diff_result.file_diffs
                ])

            # Store entity changes
            if diff_result.entity_diffs:
                self.memory_repo.bulk_create_entity_changes([
                    {
                        "change_set_id": change_set.id,
                        "entity_type": ed.entity_type,
                        "entity_name": ed.entity_name,
                        "file_path": ed.file_path,
                        "change_type": ed.change_type,
                        "previous_name": ed.previous_name,
                        "previous_file_path": ed.previous_file_path,
                        "details": ed.details,
                    }
                    for ed in diff_result.entity_diffs
                ])

            logger.info(
                f"Change set created: {len(diff_result.file_diffs)} file changes, "
                f"{len(diff_result.entity_diffs)} entity changes"
            )

        # Store entity versions for the current snapshot
        self._store_entity_versions(repository_id, snapshot.id, current_data)

        duration = round(time.time() - start_time, 3)
        logger.info(f"Snapshot created for repository {repository_id} in {duration}s")

        return snapshot

    def _build_snapshot_data(self, repository_id: int, files) -> SnapshotData:
        """Build snapshot data from current repository files and parsed entities."""
        data = SnapshotData()

        # Build file map
        for f in files:
            data.files[f.relative_path] = {
                "checksum": f.sha256_checksum,
                "language": f.language,
                "size_bytes": f.size_bytes,
            }

        # Build entity map from latest parser run
        latest_run = self.parser_repo.get_latest_parser_run(repository_id)
        if not latest_run:
            return data

        # Get all AST nodes for this repository
        nodes = self.parser_repo.get_ast_nodes_by_repository(repository_id)

        # Map file_id to relative_path
        file_id_to_path = {f.id: f.relative_path for f in files}

        for node in nodes:
            file_path = file_id_to_path.get(node.file_id, "unknown")
            entity_type = node.node_type
            entity_name = node.name or "anonymous"

            key = DiffEngine.compute_entity_key(entity_type, entity_name, file_path)

            signature = self._get_entity_signature(node)

            data.entities[key] = {
                "start_line": node.start_line,
                "end_line": node.end_line,
                "signature": signature,
                "checksum": None,
            }

        return data

    def _build_snapshot_data_from_versions(self, snapshot_id: int) -> SnapshotData:
        """Build snapshot data from stored entity versions."""
        data = SnapshotData()

        versions = self.memory_repo.get_entity_versions_by_snapshot(snapshot_id)
        for v in versions:
            if v.change_type != "deleted":
                key = DiffEngine.compute_entity_key(v.entity_type, v.entity_name, v.file_path)
                data.entities[key] = {
                    "start_line": v.start_line,
                    "end_line": v.end_line,
                    "signature": v.signature,
                    "checksum": v.checksum,
                }

                # Infer file data from entities
                if v.file_path not in data.files:
                    data.files[v.file_path] = {
                        "checksum": v.checksum,
                        "language": None,
                    }

        return data

    def _store_entity_versions(self, repository_id: int, snapshot_id: int, data: SnapshotData) -> None:
        """Store entity versions for a snapshot."""
        records = []
        for key, info in data.entities.items():
            parts = key.split(":", 2)
            entity_type, entity_name, file_path = parts[0], parts[1], parts[2]

            records.append({
                "repository_id": repository_id,
                "snapshot_id": snapshot_id,
                "entity_type": entity_type,
                "entity_name": entity_name,
                "file_path": file_path,
                "start_line": info.get("start_line"),
                "end_line": info.get("end_line"),
                "checksum": info.get("checksum"),
                "signature": info.get("signature"),
                "change_type": "created",
            })

        if records:
            self.memory_repo.bulk_create_entity_versions(records)

    def _get_entity_signature(self, node: ASTNode) -> str | None:
        """Extract a signature string from an AST node for comparison."""
        if isinstance(node, Function):
            parts = [node.name or ""]
            if node.parameters:
                parts.append(f"({node.parameters})")
            if node.return_type:
                parts.append(f"-> {node.return_type}")
            if node.is_async:
                parts.insert(0, "async")
            return " ".join(parts)

        if isinstance(node, Class):
            parts = [node.name or ""]
            if node.bases:
                parts.append(f"({node.bases})")
            if node.is_abstract:
                parts.insert(0, "abstract")
            return " ".join(parts)

        if isinstance(node, Method):
            parts = [node.name or ""]
            if node.parameters:
                parts.append(f"({node.parameters})")
            if node.return_type:
                parts.append(f"-> {node.return_type}")
            if node.is_static:
                parts.insert(0, "static")
            if node.is_async:
                parts.insert(0, "async")
            return " ".join(parts)

        if isinstance(node, Import):
            parts = []
            if node.module:
                parts.append(f"from {node.module}")
            parts.append(node.name or "")
            return " ".join(parts)

        if isinstance(node, Variable):
            parts = [node.name or ""]
            if node.var_type:
                parts.append(f": {node.var_type}")
            return " ".join(parts)

        return node.name

    def get_timeline(self, repository_id: int, limit: int = 50) -> dict:
        """Get timeline of repository evolution."""
        commits = self.memory_repo.get_commits_by_repository(repository_id, limit)
        snapshots = self.memory_repo.get_snapshots_by_repository(repository_id, limit)
        total_commits = self.memory_repo.get_commit_count(repository_id)
        total_snapshots = self.memory_repo.get_snapshot_count(repository_id)

        # Build timeline entries
        entries = []

        # Map commit hash -> snapshot
        snapshot_by_hash = {s.commit_hash: s for s in snapshots if s.commit_hash}

        # Map snapshot_id -> change_set
        change_sets = self.memory_repo.get_change_sets_by_repository(repository_id, limit)
        cs_by_snapshot = {cs.snapshot_id: cs for cs in change_sets}

        for commit in commits:
            snapshot = snapshot_by_hash.get(commit.commit_hash)
            change_set = cs_by_snapshot.get(snapshot.id) if snapshot else None

            entries.append({
                "commit": commit,
                "snapshot": snapshot,
                "change_set": change_set,
            })

        return {
            "repository_id": repository_id,
            "total_commits": total_commits,
            "total_snapshots": total_snapshots,
            "entries": entries,
        }

    def get_commits(self, repository_id: int, limit: int = 50):
        return self.memory_repo.get_commits_by_repository(repository_id, limit)

    def get_snapshots(self, repository_id: int, limit: int = 50):
        return self.memory_repo.get_snapshots_by_repository(repository_id, limit)

    def get_changes(self, repository_id: int, limit: int = 50):
        return self.memory_repo.get_change_sets_by_repository(repository_id, limit)

    def get_changes_by_commit(self, repository_id: int, commit_hash: str) -> dict | None:
        """Get detailed change set for a specific commit."""
        cs = self.memory_repo.get_change_set_by_commit(repository_id, commit_hash)
        if not cs:
            return None

        file_changes = self.memory_repo.get_file_changes_by_change_set(cs.id)
        entity_changes = self.memory_repo.get_entity_changes_by_change_set(cs.id)

        return {
            "change_set": cs,
            "file_changes": file_changes,
            "entity_changes": entity_changes,
        }

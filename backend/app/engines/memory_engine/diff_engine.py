import hashlib
import json
from dataclasses import dataclass, field
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class FileDiff:
    file_path: str
    change_type: str  # added, modified, deleted, renamed
    language: str | None = None
    previous_path: str | None = None
    previous_checksum: str | None = None
    current_checksum: str | None = None


@dataclass
class EntityDiff:
    entity_type: str  # class, function, method, variable, import, export
    entity_name: str
    file_path: str
    change_type: str  # added, modified, deleted, renamed, moved
    previous_name: str | None = None
    previous_file_path: str | None = None
    details: str | None = None


@dataclass
class SnapshotData:
    """Represents the data from a snapshot for comparison."""
    files: dict[str, dict] = field(default_factory=dict)  # path -> {checksum, language, ...}
    entities: dict[str, dict] = field(default_factory=dict)  # "type:name:path" -> {start_line, end_line, signature, checksum}


@dataclass
class DiffResult:
    file_diffs: list[FileDiff] = field(default_factory=list)
    entity_diffs: list[EntityDiff] = field(default_factory=list)
    files_added: int = 0
    files_modified: int = 0
    files_deleted: int = 0
    files_renamed: int = 0
    entities_added: int = 0
    entities_modified: int = 0
    entities_deleted: int = 0


class DiffEngine:
    """Compares two repository snapshots and generates structured change objects."""

    RENAME_SIMILARITY_THRESHOLD = 0.8

    def compare(self, previous: SnapshotData, current: SnapshotData) -> DiffResult:
        """Compare previous and current snapshot data to detect changes."""
        result = DiffResult()

        logger.info(
            f"Comparing snapshots: {len(previous.files)} files (previous) vs {len(current.files)} files (current)"
        )

        # Detect file changes
        self._detect_file_changes(previous, current, result)

        # Detect entity changes
        self._detect_entity_changes(previous, current, result)

        logger.info(
            f"Diff completed: "
            f"files: +{result.files_added} ~{result.files_modified} -{result.files_deleted} r{result.files_renamed}, "
            f"entities: +{result.entities_added} ~{result.entities_modified} -{result.entities_deleted}"
        )

        return result

    def _detect_file_changes(self, previous: SnapshotData, current: SnapshotData, result: DiffResult) -> None:
        """Detect file-level changes between snapshots."""
        prev_paths = set(previous.files.keys())
        curr_paths = set(current.files.keys())

        added_paths = curr_paths - prev_paths
        deleted_paths = prev_paths - curr_paths
        common_paths = prev_paths & curr_paths

        # Detect renames among added/deleted files
        renamed_pairs = self._detect_renames(previous, current, added_paths, deleted_paths)

        # Remove renamed files from added/deleted sets
        renamed_added = {new for _, new in renamed_pairs}
        renamed_deleted = {old for old, _ in renamed_pairs}
        added_paths -= renamed_added
        deleted_paths -= renamed_deleted

        # Added files
        for path in sorted(added_paths):
            file_info = current.files[path]
            result.file_diffs.append(FileDiff(
                file_path=path,
                change_type="added",
                language=file_info.get("language"),
                current_checksum=file_info.get("checksum"),
            ))
            result.files_added += 1

        # Deleted files
        for path in sorted(deleted_paths):
            file_info = previous.files[path]
            result.file_diffs.append(FileDiff(
                file_path=path,
                change_type="deleted",
                language=file_info.get("language"),
                previous_checksum=file_info.get("checksum"),
            ))
            result.files_deleted += 1

        # Modified files (common paths with changed checksums)
        for path in sorted(common_paths):
            prev_info = previous.files[path]
            curr_info = current.files[path]
            prev_checksum = prev_info.get("checksum")
            curr_checksum = curr_info.get("checksum")

            if prev_checksum and curr_checksum and prev_checksum != curr_checksum:
                result.file_diffs.append(FileDiff(
                    file_path=path,
                    change_type="modified",
                    language=curr_info.get("language"),
                    previous_checksum=prev_checksum,
                    current_checksum=curr_checksum,
                ))
                result.files_modified += 1

        # Renamed files
        for old_path, new_path in renamed_pairs:
            curr_info = current.files[new_path]
            prev_info = previous.files[old_path]
            result.file_diffs.append(FileDiff(
                file_path=new_path,
                change_type="renamed",
                language=curr_info.get("language"),
                previous_path=old_path,
                previous_checksum=prev_info.get("checksum"),
                current_checksum=curr_info.get("checksum"),
            ))
            result.files_renamed += 1

    def _detect_renames(
        self, previous: SnapshotData, current: SnapshotData,
        added_paths: set[str], deleted_paths: set[str]
    ) -> list[tuple[str, str]]:
        """Detect file renames by matching checksums of added and deleted files."""
        renamed_pairs = []

        if not added_paths or not deleted_paths:
            return renamed_pairs

        # Build checksum -> path map for deleted files
        deleted_by_checksum: dict[str, str] = {}
        for path in deleted_paths:
            checksum = previous.files[path].get("checksum")
            if checksum:
                deleted_by_checksum[checksum] = path

        # Match added files with deleted files by checksum
        for path in list(added_paths):
            checksum = current.files[path].get("checksum")
            if checksum and checksum in deleted_by_checksum:
                old_path = deleted_by_checksum.pop(checksum)
                renamed_pairs.append((old_path, path))

        return renamed_pairs

    def _detect_entity_changes(self, previous: SnapshotData, current: SnapshotData, result: DiffResult) -> None:
        """Detect entity-level changes between snapshots."""
        prev_keys = set(previous.entities.keys())
        curr_keys = set(current.entities.keys())

        added_keys = curr_keys - prev_keys
        deleted_keys = prev_keys - curr_keys
        common_keys = prev_keys & curr_keys

        # Detect entity renames/moves among added/deleted
        entity_renames = self._detect_entity_renames(previous, current, added_keys, deleted_keys)

        renamed_added = {new for _, new in entity_renames}
        renamed_deleted = {old for old, _ in entity_renames}
        added_keys -= renamed_added
        deleted_keys -= renamed_deleted

        # Added entities
        for key in sorted(added_keys):
            parts = key.split(":", 2)
            entity_type, entity_name, file_path = parts[0], parts[1], parts[2]
            result.entity_diffs.append(EntityDiff(
                entity_type=entity_type,
                entity_name=entity_name,
                file_path=file_path,
                change_type="added",
            ))
            result.entities_added += 1

        # Deleted entities
        for key in sorted(deleted_keys):
            parts = key.split(":", 2)
            entity_type, entity_name, file_path = parts[0], parts[1], parts[2]
            result.entity_diffs.append(EntityDiff(
                entity_type=entity_type,
                entity_name=entity_name,
                file_path=file_path,
                change_type="deleted",
            ))
            result.entities_deleted += 1

        # Modified entities (same key but different signature/checksum)
        for key in sorted(common_keys):
            prev_info = previous.entities[key]
            curr_info = current.entities[key]

            prev_sig = prev_info.get("signature")
            curr_sig = curr_info.get("signature")
            prev_cs = prev_info.get("checksum")
            curr_cs = curr_info.get("checksum")

            if (prev_sig != curr_sig) or (prev_cs and curr_cs and prev_cs != curr_cs):
                parts = key.split(":", 2)
                entity_type, entity_name, file_path = parts[0], parts[1], parts[2]

                changes = []
                if prev_info.get("start_line") != curr_info.get("start_line"):
                    changes.append("line_changed")
                if prev_sig != curr_sig:
                    changes.append("signature_changed")

                result.entity_diffs.append(EntityDiff(
                    entity_type=entity_type,
                    entity_name=entity_name,
                    file_path=file_path,
                    change_type="modified",
                    details=json.dumps({"changes": changes}) if changes else None,
                ))
                result.entities_modified += 1

        # Renamed/moved entities
        for old_key, new_key in entity_renames:
            old_parts = old_key.split(":", 2)
            new_parts = new_key.split(":", 2)

            if old_parts[2] != new_parts[2]:
                change_type = "moved"
            else:
                change_type = "renamed"

            result.entity_diffs.append(EntityDiff(
                entity_type=new_parts[0],
                entity_name=new_parts[1],
                file_path=new_parts[2],
                change_type=change_type,
                previous_name=old_parts[1] if old_parts[1] != new_parts[1] else None,
                previous_file_path=old_parts[2] if old_parts[2] != new_parts[2] else None,
            ))

    def _detect_entity_renames(
        self, previous: SnapshotData, current: SnapshotData,
        added_keys: set[str], deleted_keys: set[str]
    ) -> list[tuple[str, str]]:
        """Detect entity renames/moves by matching signatures."""
        renames = []

        if not added_keys or not deleted_keys:
            return renames

        # Build signature map for deleted entities
        deleted_by_sig: dict[str, str] = {}
        for key in deleted_keys:
            sig = previous.entities[key].get("signature")
            entity_type = key.split(":", 2)[0]
            if sig:
                sig_key = f"{entity_type}:{sig}"
                deleted_by_sig[sig_key] = key

        for key in list(added_keys):
            sig = current.entities[key].get("signature")
            entity_type = key.split(":", 2)[0]
            if sig:
                sig_key = f"{entity_type}:{sig}"
                if sig_key in deleted_by_sig:
                    old_key = deleted_by_sig.pop(sig_key)
                    renames.append((old_key, key))

        return renames

    @staticmethod
    def compute_entity_key(entity_type: str, entity_name: str, file_path: str) -> str:
        """Compute a unique key for an entity."""
        return f"{entity_type}:{entity_name}:{file_path}"

    @staticmethod
    def compute_content_checksum(content: str) -> str:
        """Compute SHA256 checksum of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

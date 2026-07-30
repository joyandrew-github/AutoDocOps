"""Unit tests for the DiffEngine."""
import pytest
from app.engines.memory_engine.diff_engine import DiffEngine, SnapshotData


class TestDiffEngine:
    """Test DiffEngine snapshot comparison logic."""

    @pytest.fixture
    def engine(self):
        return DiffEngine()

    @pytest.fixture
    def empty_snapshot(self):
        return SnapshotData()

    # --- File-level diff tests ---

    def test_no_changes(self, engine):
        """Test comparison of identical snapshots produces no diffs."""
        prev = SnapshotData(
            files={"src/main.py": {"checksum": "abc123", "language": "Python"}},
            entities={"function:main:src/main.py": {"signature": "main()", "start_line": 1}},
        )
        curr = SnapshotData(
            files={"src/main.py": {"checksum": "abc123", "language": "Python"}},
            entities={"function:main:src/main.py": {"signature": "main()", "start_line": 1}},
        )
        result = engine.compare(prev, curr)

        assert result.files_added == 0
        assert result.files_modified == 0
        assert result.files_deleted == 0
        assert result.files_renamed == 0
        assert result.entities_added == 0
        assert result.entities_modified == 0
        assert result.entities_deleted == 0
        assert len(result.file_diffs) == 0
        assert len(result.entity_diffs) == 0

    def test_added_files(self, engine, empty_snapshot):
        """Test detection of newly added files."""
        curr = SnapshotData(
            files={
                "src/main.py": {"checksum": "abc123", "language": "Python"},
                "src/utils.py": {"checksum": "def456", "language": "Python"},
            }
        )
        result = engine.compare(empty_snapshot, curr)

        assert result.files_added == 2
        assert result.files_deleted == 0
        assert result.files_modified == 0
        assert len(result.file_diffs) == 2
        assert all(d.change_type == "added" for d in result.file_diffs)

    def test_deleted_files(self, engine, empty_snapshot):
        """Test detection of deleted files."""
        prev = SnapshotData(
            files={
                "src/main.py": {"checksum": "abc123", "language": "Python"},
                "src/old.py": {"checksum": "xyz789", "language": "Python"},
            }
        )
        result = engine.compare(prev, empty_snapshot)

        assert result.files_deleted == 2
        assert result.files_added == 0
        assert len(result.file_diffs) == 2
        assert all(d.change_type == "deleted" for d in result.file_diffs)

    def test_modified_files(self, engine):
        """Test detection of modified files (changed checksums)."""
        prev = SnapshotData(
            files={"src/main.py": {"checksum": "abc123", "language": "Python"}}
        )
        curr = SnapshotData(
            files={"src/main.py": {"checksum": "new456", "language": "Python"}}
        )
        result = engine.compare(prev, curr)

        assert result.files_modified == 1
        assert result.files_added == 0
        assert result.files_deleted == 0
        assert result.file_diffs[0].change_type == "modified"
        assert result.file_diffs[0].previous_checksum == "abc123"
        assert result.file_diffs[0].current_checksum == "new456"

    def test_renamed_files(self, engine):
        """Test detection of renamed files (same checksum, different path)."""
        prev = SnapshotData(
            files={"src/old_name.py": {"checksum": "abc123", "language": "Python"}}
        )
        curr = SnapshotData(
            files={"src/new_name.py": {"checksum": "abc123", "language": "Python"}}
        )
        result = engine.compare(prev, curr)

        assert result.files_renamed == 1
        assert result.files_added == 0
        assert result.files_deleted == 0
        assert result.file_diffs[0].change_type == "renamed"
        assert result.file_diffs[0].previous_path == "src/old_name.py"
        assert result.file_diffs[0].file_path == "src/new_name.py"

    def test_mixed_file_changes(self, engine):
        """Test detection of mixed file changes."""
        prev = SnapshotData(
            files={
                "src/keep.py": {"checksum": "aaa", "language": "Python"},
                "src/modify.py": {"checksum": "bbb", "language": "Python"},
                "src/delete.py": {"checksum": "ccc", "language": "Python"},
                "src/rename_old.py": {"checksum": "ddd", "language": "Python"},
            }
        )
        curr = SnapshotData(
            files={
                "src/keep.py": {"checksum": "aaa", "language": "Python"},
                "src/modify.py": {"checksum": "bbb_new", "language": "Python"},
                "src/add.py": {"checksum": "eee", "language": "Python"},
                "src/rename_new.py": {"checksum": "ddd", "language": "Python"},
            }
        )
        result = engine.compare(prev, curr)

        assert result.files_added == 1
        assert result.files_modified == 1
        assert result.files_deleted == 1
        assert result.files_renamed == 1

    # --- Entity-level diff tests ---

    def test_added_entities(self, engine):
        """Test detection of new entities."""
        prev = SnapshotData()
        curr = SnapshotData(
            entities={
                "function:hello:src/main.py": {"signature": "hello()", "start_line": 1},
                "class:MyClass:src/main.py": {"signature": "MyClass", "start_line": 5},
            }
        )
        result = engine.compare(prev, curr)

        assert result.entities_added == 2
        assert result.entities_deleted == 0
        assert result.entities_modified == 0

    def test_deleted_entities(self, engine):
        """Test detection of deleted entities."""
        prev = SnapshotData(
            entities={
                "function:hello:src/main.py": {"signature": "hello()", "start_line": 1},
            }
        )
        curr = SnapshotData()
        result = engine.compare(prev, curr)

        assert result.entities_deleted == 1
        assert result.entities_added == 0

    def test_modified_entities(self, engine):
        """Test detection of modified entities (changed signature)."""
        prev = SnapshotData(
            entities={
                "function:calc:src/math.py": {"signature": "calc(x)", "start_line": 1},
            }
        )
        curr = SnapshotData(
            entities={
                "function:calc:src/math.py": {"signature": "calc(x, y)", "start_line": 1},
            }
        )
        result = engine.compare(prev, curr)

        assert result.entities_modified == 1
        assert result.entity_diffs[0].change_type == "modified"
        assert result.entity_diffs[0].entity_name == "calc"

    def test_renamed_entities(self, engine):
        """Test detection of renamed entities (same signature, different name)."""
        prev = SnapshotData(
            entities={
                "function:old_name:src/main.py": {"signature": "old_name(x, y)", "start_line": 1},
            }
        )
        curr = SnapshotData(
            entities={
                "function:new_name:src/main.py": {"signature": "old_name(x, y)", "start_line": 1},
            }
        )
        result = engine.compare(prev, curr)

        # Should detect as rename via signature matching
        renamed_diffs = [d for d in result.entity_diffs if d.change_type == "renamed"]
        assert len(renamed_diffs) == 1
        assert renamed_diffs[0].entity_name == "new_name"
        assert renamed_diffs[0].previous_name == "old_name"

    def test_moved_entities(self, engine):
        """Test detection of moved entities (same signature, different file)."""
        prev = SnapshotData(
            entities={
                "function:helper:src/utils.py": {"signature": "helper(data)", "start_line": 1},
            }
        )
        curr = SnapshotData(
            entities={
                "function:helper:src/helpers.py": {"signature": "helper(data)", "start_line": 1},
            }
        )
        result = engine.compare(prev, curr)

        moved_diffs = [d for d in result.entity_diffs if d.change_type == "moved"]
        assert len(moved_diffs) == 1
        assert moved_diffs[0].previous_file_path == "src/utils.py"
        assert moved_diffs[0].file_path == "src/helpers.py"

    def test_entity_line_change_is_modification(self, engine):
        """Test that entities with changed line numbers are detected as modified."""
        prev = SnapshotData(
            entities={
                "function:calc:src/math.py": {"signature": "calc(x)", "start_line": 1, "checksum": "aaa"},
            }
        )
        curr = SnapshotData(
            entities={
                "function:calc:src/math.py": {"signature": "calc(x)", "start_line": 10, "checksum": "bbb"},
            }
        )
        result = engine.compare(prev, curr)

        assert result.entities_modified == 1

    # --- Utility tests ---

    def test_compute_entity_key(self):
        key = DiffEngine.compute_entity_key("function", "main", "src/main.py")
        assert key == "function:main:src/main.py"

    def test_compute_content_checksum(self):
        cs = DiffEngine.compute_content_checksum("hello world")
        assert len(cs) == 64  # SHA256 hex digest

    def test_compare_empty_snapshots(self, engine, empty_snapshot):
        """Test comparing two empty snapshots."""
        result = engine.compare(empty_snapshot, empty_snapshot)
        assert result.files_added == 0
        assert result.files_deleted == 0
        assert result.entities_added == 0
        assert result.entities_deleted == 0

    def test_unchanged_entities_not_reported(self, engine):
        """Test that unchanged entities are not reported as changes."""
        data = SnapshotData(
            entities={
                "function:a:f.py": {"signature": "a()", "start_line": 1, "checksum": "x"},
                "function:b:f.py": {"signature": "b()", "start_line": 5, "checksum": "y"},
            }
        )
        result = engine.compare(data, data)
        assert len(result.entity_diffs) == 0

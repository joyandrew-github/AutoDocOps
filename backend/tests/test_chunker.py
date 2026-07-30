"""Unit tests for the CodeChunker."""
import pytest
from app.engines.vector_engine.chunker import CodeChunker, Chunk


class TestCodeChunker:
    """Test CodeChunker text splitting logic."""

    @pytest.fixture
    def chunker(self):
        return CodeChunker(chunk_size=10, chunk_overlap=2)

    def test_empty_text(self, chunker):
        result = chunker.chunk_text("")
        assert result == []

    def test_whitespace_only(self, chunker):
        result = chunker.chunk_text("   \n  ")
        assert result == []

    def test_single_small_chunk(self, chunker):
        result = chunker.chunk_text("hello world")
        assert len(result) == 1
        assert result[0].chunk_index == 0
        assert "hello world" in result[0].text

    def test_multiple_chunks(self, chunker):
        # Create text with more than 10 words per chunk
        lines = ["word " * 8 for _ in range(5)]
        text = "\n".join(lines)
        result = chunker.chunk_text(text)
        assert len(result) > 1

    def test_chunk_indexes_sequential(self, chunker):
        lines = ["word " * 8 for _ in range(5)]
        text = "\n".join(lines)
        result = chunker.chunk_text(text)
        for i, chunk in enumerate(result):
            assert chunk.chunk_index == i

    def test_chunk_has_content_hash(self, chunker):
        result = chunker.chunk_text("hello world")
        assert result[0].content_hash != ""
        assert len(result[0].content_hash) == 64

    def test_chunk_line_numbers(self, chunker):
        result = chunker.chunk_text("line one\nline two\nline three", start_line=10)
        assert result[0].start_line == 10

    def test_chunk_token_count(self, chunker):
        result = chunker.chunk_text("one two three four")
        assert result[0].token_count == 4

    def test_chunk_text_with_start_line(self, chunker):
        result = chunker.chunk_text("hello world", start_line=5)
        assert result[0].start_line == 5

    def test_chunk_code_entity_small(self, chunker):
        result = chunker.chunk_code_entity(
            name="my_func",
            entity_type="function",
            source="def my_func(): pass",
            file_path="main.py",
            language="Python",
            start_line=1,
        )
        assert len(result) >= 1
        assert "function" in result[0].text.lower() or "my_func" in result[0].text

    def test_chunk_code_entity_large(self):
        chunker = CodeChunker(chunk_size=5, chunk_overlap=1)
        source = "\n".join([f"line {i} with some words here" for i in range(20)])
        result = chunker.chunk_code_entity(
            name="big_func",
            entity_type="function",
            source=source,
        )
        assert len(result) > 1

    def test_build_embedding_text(self, chunker):
        text = chunker.build_embedding_text(
            entity_type="function",
            entity_name="process",
            content="def process(): pass",
            file_path="utils.py",
            language="Python",
            docstring="Process items.",
            signature="def process()",
        )
        assert "function" in text.lower() or "Type: function" in text
        assert "process" in text
        assert "utils.py" in text
        assert "Python" in text
        assert "Process items." in text

    def test_build_embedding_text_minimal(self, chunker):
        text = chunker.build_embedding_text(
            entity_type="variable",
            entity_name="x",
            content="x = 1",
        )
        assert "variable" in text.lower() or "Type: variable" in text
        assert "x" in text

    def test_count_tokens(self, chunker):
        assert CodeChunker._count_tokens("a b c") == 3
        assert CodeChunker._count_tokens("") == 0


class TestChunkDataclass:
    """Test the Chunk dataclass."""

    def test_auto_content_hash(self):
        c = Chunk(text="hello", chunk_index=0, token_count=1)
        assert c.content_hash != ""
        assert len(c.content_hash) == 64

    def test_explicit_content_hash(self):
        c = Chunk(text="hello", chunk_index=0, token_count=1, content_hash="custom")
        assert c.content_hash == "custom"

    def test_defaults(self):
        c = Chunk(text="x", chunk_index=0, token_count=1)
        assert c.start_line is None
        assert c.end_line is None

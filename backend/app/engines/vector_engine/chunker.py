"""Semantic code chunker — splits large texts into meaningful chunks."""
import hashlib
from dataclasses import dataclass, field
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class Chunk:
    """Represents a single text chunk."""
    text: str
    chunk_index: int
    token_count: int
    start_line: int | None = None
    end_line: int | None = None
    content_hash: str = ""

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.text.encode()).hexdigest()


class CodeChunker:
    """Splits source code and text into semantic chunks respecting boundaries."""

    def __init__(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_text(self, text: str, start_line: int | None = None) -> list[Chunk]:
        """Split text into chunks by token count, respecting line boundaries."""
        if not text or not text.strip():
            return []

        lines = text.split("\n")
        chunks: list[Chunk] = []
        current_lines: list[str] = []
        current_tokens = 0
        chunk_start_line = start_line or 1

        for i, line in enumerate(lines):
            line_tokens = self._count_tokens(line)

            if current_tokens + line_tokens > self.chunk_size and current_lines:
                chunk_text = "\n".join(current_lines)
                chunks.append(Chunk(
                    text=chunk_text,
                    chunk_index=len(chunks),
                    token_count=current_tokens,
                    start_line=chunk_start_line,
                    end_line=chunk_start_line + len(current_lines) - 1,
                ))

                # Keep overlap lines
                overlap_lines: list[str] = []
                overlap_tokens = 0
                for ol in reversed(current_lines):
                    ol_tokens = self._count_tokens(ol)
                    if overlap_tokens + ol_tokens > self.chunk_overlap:
                        break
                    overlap_lines.insert(0, ol)
                    overlap_tokens += ol_tokens

                current_lines = overlap_lines
                current_tokens = overlap_tokens
                chunk_start_line = chunk_start_line + len(current_lines)

            current_lines.append(line)
            current_tokens += line_tokens

        # Final chunk
        if current_lines:
            chunk_text = "\n".join(current_lines)
            chunks.append(Chunk(
                text=chunk_text,
                chunk_index=len(chunks),
                token_count=current_tokens,
                start_line=chunk_start_line,
                end_line=chunk_start_line + len(current_lines) - 1,
            ))

        return chunks

    def chunk_code_entity(
        self,
        name: str,
        entity_type: str,
        source: str,
        file_path: str | None = None,
        language: str | None = None,
        start_line: int | None = None,
    ) -> list[Chunk]:
        """Chunk a code entity, prepending context metadata."""
        prefix_parts = []
        if language:
            prefix_parts.append(f"Language: {language}")
        if file_path:
            prefix_parts.append(f"File: {file_path}")
        prefix_parts.append(f"{entity_type}: {name}")
        prefix = "\n".join(prefix_parts) + "\n\n"

        total_tokens = self._count_tokens(prefix + source)

        if total_tokens <= self.chunk_size:
            return [Chunk(
                text=prefix + source,
                chunk_index=0,
                token_count=total_tokens,
                start_line=start_line,
                end_line=(start_line + source.count("\n")) if start_line else None,
            )]

        return self.chunk_text(prefix + source, start_line=start_line)

    def build_embedding_text(
        self,
        entity_type: str,
        entity_name: str,
        content: str,
        file_path: str | None = None,
        language: str | None = None,
        docstring: str | None = None,
        signature: str | None = None,
    ) -> str:
        """Build a rich text representation for embedding."""
        parts = []
        if language:
            parts.append(f"Language: {language}")
        if file_path:
            parts.append(f"File: {file_path}")
        parts.append(f"Type: {entity_type}")
        parts.append(f"Name: {entity_name}")
        if signature:
            parts.append(f"Signature: {signature}")
        if docstring:
            parts.append(f"Documentation: {docstring}")
        parts.append("")
        parts.append(content)
        return "\n".join(parts)

    @staticmethod
    def _count_tokens(text: str) -> int:
        """Estimate token count (words-based approximation)."""
        return len(text.split())

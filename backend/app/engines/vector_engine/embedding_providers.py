"""Pluggable embedding provider interface and implementations."""
import hashlib
import struct
from abc import ABC, abstractmethod
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseEmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model identifier."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Output embedding dimension."""
        ...

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text."""
        ...

    @abstractmethod
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for a batch of texts."""
        ...

    def count_tokens(self, text: str) -> int:
        """Estimate token count for a text. Override for accurate counting."""
        return len(text.split())


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic mock provider for testing — produces reproducible vectors from text hash."""

    @property
    def name(self) -> str:
        return "mock"

    @property
    def model_name(self) -> str:
        return "mock-embedding-v1"

    @property
    def dimension(self) -> int:
        return settings.EMBEDDING_DIMENSION

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        vector = []
        for i in range(self.dimension):
            byte_idx = i % len(digest)
            vector.append((digest[byte_idx] / 255.0) * 2 - 1)
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    def count_tokens(self, text: str) -> int:
        return len(text.split())


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embeddings provider using the official API."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embedding provider")
        try:
            import openai
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        except ImportError:
            raise ImportError("openai package is required: pip install openai")
        try:
            import tiktoken
            self._encoding = tiktoken.encoding_for_model(settings.OPENAI_EMBEDDING_MODEL)
        except (ImportError, KeyError):
            self._encoding = None

    @property
    def name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return settings.OPENAI_EMBEDDING_MODEL

    @property
    def dimension(self) -> int:
        return settings.EMBEDDING_DIMENSION

    def embed_text(self, text: str) -> list[float]:
        text = text.replace("\n", " ").strip()
        if not text:
            return [0.0] * self.dimension
        try:
            response = self._client.embeddings.create(
                input=[text],
                model=self.model_name,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            raise

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        cleaned = [t.replace("\n", " ").strip() or " " for t in texts]
        try:
            response = self._client.embeddings.create(
                input=cleaned,
                model=self.model_name,
            )
            return [d.embedding for d in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {e}")
            raise

    def count_tokens(self, text: str) -> int:
        if self._encoding:
            return len(self._encoding.encode(text))
        return len(text.split())


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local embedding provider using a simple hash-based approach.

    For production, swap the embed logic with a local model (e.g. sentence-transformers).
    """

    @property
    def name(self) -> str:
        return "local"

    @property
    def model_name(self) -> str:
        return "local-hash-v1"

    @property
    def dimension(self) -> int:
        return settings.EMBEDDING_DIMENSION

    def embed_text(self, text: str) -> list[float]:
        digest = hashlib.sha512(text.encode()).digest()
        vector = []
        for i in range(self.dimension):
            idx = (i * 4) % len(digest)
            b = digest[idx]
            vector.append((b / 255.0) * 2 - 1)
        norm = sum(v * v for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]

    def count_tokens(self, text: str) -> int:
        return len(text.split())


def get_embedding_provider() -> BaseEmbeddingProvider:
    """Factory function returning the configured embedding provider."""
    provider_name = settings.EMBEDDING_PROVIDER.lower()
    if provider_name == "openai":
        return OpenAIEmbeddingProvider()
    elif provider_name == "local":
        return LocalEmbeddingProvider()
    else:
        return MockEmbeddingProvider()

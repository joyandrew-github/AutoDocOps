"""Unit tests for embedding providers."""
import pytest
from unittest.mock import patch, MagicMock
from app.engines.vector_engine.embedding_providers import (
    BaseEmbeddingProvider,
    MockEmbeddingProvider,
    LocalEmbeddingProvider,
    get_embedding_provider,
)


class TestMockEmbeddingProvider:
    """Test MockEmbeddingProvider."""

    @pytest.fixture
    def provider(self):
        return MockEmbeddingProvider()

    def test_name(self, provider):
        assert provider.name == "mock"

    def test_model_name(self, provider):
        assert provider.model_name == "mock-embedding-v1"

    def test_dimension(self, provider):
        assert provider.dimension > 0

    def test_embed_text_returns_list(self, provider):
        result = provider.embed_text("hello world")
        assert isinstance(result, list)
        assert len(result) == provider.dimension

    def test_embed_text_deterministic(self, provider):
        v1 = provider.embed_text("hello world")
        v2 = provider.embed_text("hello world")
        assert v1 == v2

    def test_embed_text_different_inputs_different_vectors(self, provider):
        v1 = provider.embed_text("hello world")
        v2 = provider.embed_text("goodbye world")
        assert v1 != v2

    def test_embed_text_normalized(self, provider):
        v = provider.embed_text("test")
        norm = sum(x * x for x in v) ** 0.5
        assert abs(norm - 1.0) < 0.01

    def test_embed_batch(self, provider):
        texts = ["hello", "world", "test"]
        results = provider.embed_batch(texts)
        assert len(results) == 3
        assert all(len(v) == provider.dimension for v in results)

    def test_embed_batch_empty(self, provider):
        results = provider.embed_batch([])
        assert results == []

    def test_count_tokens(self, provider):
        count = provider.count_tokens("one two three")
        assert count == 3


class TestLocalEmbeddingProvider:
    """Test LocalEmbeddingProvider."""

    @pytest.fixture
    def provider(self):
        return LocalEmbeddingProvider()

    def test_name(self, provider):
        assert provider.name == "local"

    def test_model_name(self, provider):
        assert provider.model_name == "local-hash-v1"

    def test_embed_text(self, provider):
        result = provider.embed_text("test code")
        assert len(result) == provider.dimension

    def test_embed_text_deterministic(self, provider):
        v1 = provider.embed_text("same text")
        v2 = provider.embed_text("same text")
        assert v1 == v2

    def test_embed_text_normalized(self, provider):
        v = provider.embed_text("test")
        norm = sum(x * x for x in v) ** 0.5
        assert abs(norm - 1.0) < 0.01

    def test_embed_batch(self, provider):
        results = provider.embed_batch(["a", "b"])
        assert len(results) == 2

    def test_count_tokens(self, provider):
        assert provider.count_tokens("a b c d") == 4


class TestGetEmbeddingProvider:
    """Test provider factory function."""

    def test_default_is_mock(self):
        with patch("app.engines.vector_engine.embedding_providers.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "mock"
            mock_settings.EMBEDDING_DIMENSION = 1536
            provider = get_embedding_provider()
            assert provider.name == "mock"

    def test_local_provider(self):
        with patch("app.engines.vector_engine.embedding_providers.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "local"
            mock_settings.EMBEDDING_DIMENSION = 1536
            provider = get_embedding_provider()
            assert provider.name == "local"

    def test_unknown_provider_defaults_to_mock(self):
        with patch("app.engines.vector_engine.embedding_providers.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "unknown"
            mock_settings.EMBEDDING_DIMENSION = 1536
            provider = get_embedding_provider()
            assert provider.name == "mock"


class TestBaseEmbeddingProvider:
    """Test that BaseEmbeddingProvider is abstract."""

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseEmbeddingProvider()

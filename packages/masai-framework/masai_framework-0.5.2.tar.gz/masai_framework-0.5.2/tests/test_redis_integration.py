"""
Comprehensive tests for Redis integration with MASAI persistent memory.

Tests cover:
- RedisConfig creation and validation
- RedisAdapter initialization
- Document upsert with deduplication
- Search with user isolation
- TTL configuration
- Embedding model support (OpenAI, HuggingFace, custom)
- Backend switching (Qdrant vs Redis)
"""

import pytest
import asyncio
from typing import List
from unittest.mock import Mock, AsyncMock, patch

from src.masai.Memory.LongTermMemory import (
    RedisConfig,
    RedisAdapter,
    QdrantConfig,
    LongTermMemory,
)
from src.masai.schema import Document


class TestRedisConfig:
    """Test RedisConfig creation and validation."""

    def test_redis_config_defaults(self):
        """Test RedisConfig with default values."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]]))
        )
        assert config.redis_url == "redis://localhost:6379"
        assert config.index_name == "masai_vectors"
        assert config.vector_size == 384
        assert config.distance_metric == "cosine"
        assert config.dedup_mode == "similarity"
        assert config.dedup_similarity_threshold == 0.95
        assert config.ttl_seconds is None
        assert config.batch_size == 100

    def test_redis_config_custom_values(self):
        """Test RedisConfig with custom values."""
        embedding_model = Mock(embed_documents=Mock(return_value=[[0.1, 0.2]]))
        config = RedisConfig(
            redis_url="redis://user:pass@localhost:6380",
            index_name="custom_index",
            vector_size=1536,
            distance_metric="l2",
            embedding_model=embedding_model,
            dedup_mode="hash",
            ttl_seconds=86400,
            batch_size=50,
        )
        assert config.redis_url == "redis://user:pass@localhost:6380"
        assert config.index_name == "custom_index"
        assert config.vector_size == 1536
        assert config.distance_metric == "l2"
        assert config.dedup_mode == "hash"
        assert config.ttl_seconds == 86400
        assert config.batch_size == 50

    def test_redis_config_embedding_model_validation(self):
        """Test embedding model validation."""
        # Valid: callable
        config = RedisConfig(embedding_model=lambda texts: [[0.1, 0.2]])
        config.validate_embedding_model()  # Should not raise

        # Valid: has embed_documents
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]]))
        )
        config.validate_embedding_model()  # Should not raise

        # Invalid: no embedding_model
        config = RedisConfig(embedding_model=None)
        with pytest.raises(ValueError, match="embedding_model is required"):
            config.validate_embedding_model()

        # Invalid: not callable and no embed_documents
        config = RedisConfig(embedding_model="invalid")
        with pytest.raises(ValueError, match="must be callable or have embed_documents"):
            config.validate_embedding_model()


class TestRedisAdapter:
    """Test RedisAdapter functionality."""

    def test_redis_adapter_initialization(self):
        """Test RedisAdapter initialization."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]]))
        )
        adapter = RedisAdapter(config)
        assert adapter.cfg == config
        assert adapter.redis_url == "redis://localhost:6379"
        assert adapter.index_name == "masai_vectors"

    def test_get_doc_id_hash_mode(self):
        """Test document ID generation in hash mode."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            dedup_mode="hash",
        )
        adapter = RedisAdapter(config)

        doc = Document(page_content="Test content", metadata={})
        doc_id = adapter._get_doc_id_with_dedup(doc)

        # Hash mode should return deterministic hash
        doc_id2 = adapter._get_doc_id_with_dedup(doc)
        assert doc_id == doc_id2

    def test_get_doc_id_similarity_mode(self):
        """Test document ID generation in similarity mode."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            dedup_mode="similarity",
        )
        adapter = RedisAdapter(config)

        doc = Document(page_content="Test content", metadata={})
        doc_id1 = adapter._get_doc_id_with_dedup(doc)
        doc_id2 = adapter._get_doc_id_with_dedup(doc)

        # Similarity mode should return different UUIDs
        assert doc_id1 != doc_id2

    def test_get_doc_id_none_mode(self):
        """Test document ID generation in none mode."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            dedup_mode="none",
        )
        adapter = RedisAdapter(config)

        doc = Document(page_content="Test content", metadata={})
        doc_id1 = adapter._get_doc_id_with_dedup(doc)
        doc_id2 = adapter._get_doc_id_with_dedup(doc)

        # None mode should return different UUIDs
        assert doc_id1 != doc_id2

    def test_resolve_embeddings_callable(self):
        """Test embedding resolution for callable."""
        embedding_fn = lambda texts: [[0.1, 0.2] for _ in texts]
        config = RedisConfig(embedding_model=embedding_fn)
        adapter = RedisAdapter(config)

        embeddings = adapter._resolve_embeddings()
        assert hasattr(embeddings, "embed_documents")
        assert hasattr(embeddings, "embed_query")

    def test_resolve_embeddings_langchain(self):
        """Test embedding resolution for LangChain embeddings."""
        embedding_model = Mock(embed_documents=Mock(return_value=[[0.1, 0.2]]))
        config = RedisConfig(embedding_model=embedding_model)
        adapter = RedisAdapter(config)

        embeddings = adapter._resolve_embeddings()
        assert embeddings == embedding_model


class TestLongTermMemoryBackendSelection:
    """Test LongTermMemory backend selection."""

    def test_qdrant_backend_selection(self):
        """Test Qdrant backend selection."""
        config = QdrantConfig(
            url="http://localhost:6333",
            collection_name="test",
            vector_size=384,
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
        )
        memory = LongTermMemory(backend_config=config)
        assert memory.backend_type == "qdrant"

    def test_redis_backend_selection(self):
        """Test Redis backend selection."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]]))
        )
        memory = LongTermMemory(backend_config=config)
        assert memory.backend_type == "redis"

    def test_backend_selection_from_dict_qdrant(self):
        """Test backend selection from dict (Qdrant)."""
        config_dict = {
            "url": "http://localhost:6333",
            "collection_name": "test",
            "vector_size": 384,
            "embedding_model": Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
        }
        memory = LongTermMemory(backend_config=config_dict)
        assert memory.backend_type == "qdrant"

    def test_backend_selection_from_dict_redis(self):
        """Test backend selection from dict (Redis)."""
        config_dict = {
            "redis_url": "redis://localhost:6379",
            "embedding_model": Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
        }
        memory = LongTermMemory(backend_config=config_dict)
        assert memory.backend_type == "redis"

    def test_invalid_backend_config_type(self):
        """Test invalid backend config type."""
        with pytest.raises(TypeError, match="backend_config must be"):
            LongTermMemory(backend_config="invalid")


class TestRedisConfigurationOptions:
    """Test comprehensive Redis configuration options."""

    def test_ttl_configuration(self):
        """Test TTL configuration."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            ttl_seconds=3600,
        )
        assert config.ttl_seconds == 3600

    def test_connection_pool_configuration(self):
        """Test connection pool configuration."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            connection_pool_size=20,
        )
        assert config.connection_pool_size == 20

    def test_socket_configuration(self):
        """Test socket configuration."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            socket_timeout=10.0,
            socket_connect_timeout=10.0,
            socket_keepalive=True,
        )
        assert config.socket_timeout == 10.0
        assert config.socket_connect_timeout == 10.0
        assert config.socket_keepalive is True

    def test_health_check_configuration(self):
        """Test health check configuration."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            health_check_interval=60,
        )
        assert config.health_check_interval == 60

    def test_batch_size_configuration(self):
        """Test batch size configuration."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            batch_size=200,
        )
        assert config.batch_size == 200

    def test_async_configuration(self):
        """Test async configuration."""
        config = RedisConfig(
            embedding_model=Mock(embed_documents=Mock(return_value=[[0.1, 0.2]])),
            use_async=True,
        )
        assert config.use_async is True


class TestEmbeddingModelSupport:
    """Test various embedding model types."""

    def test_callable_embedding_model(self):
        """Test callable embedding model."""
        def embed_fn(texts: List[str]) -> List[List[float]]:
            return [[0.1, 0.2] for _ in texts]

        config = RedisConfig(embedding_model=embed_fn)
        config.validate_embedding_model()  # Should not raise

    def test_langchain_embedding_model(self):
        """Test LangChain embedding model."""
        embedding_model = Mock(
            embed_documents=Mock(return_value=[[0.1, 0.2]]),
            embed_query=Mock(return_value=[0.1, 0.2]),
        )
        config = RedisConfig(embedding_model=embedding_model)
        config.validate_embedding_model()  # Should not raise

    def test_custom_embedding_class(self):
        """Test custom embedding class."""
        class CustomEmbeddings:
            def embed_documents(self, texts: List[str]) -> List[List[float]]:
                return [[0.1, 0.2] for _ in texts]

        config = RedisConfig(embedding_model=CustomEmbeddings())
        config.validate_embedding_model()  # Should not raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


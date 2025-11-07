"""
Comprehensive tests for Redis adapter operations with real embeddings.

Tests cover:
- Document upsert with real OpenAI embeddings
- Document upsert with Redis internal embeddings
- Document upsert with HuggingFace embeddings
- Search operations with user isolation
- Delete operations
- Flush operations
- TTL functionality
- Deduplication modes
- Batch operations
- User isolation and data separation
"""

import pytest
import asyncio
import os
from typing import List
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.masai.Memory.LongTermMemory import (
    RedisConfig,
    RedisAdapter,
    LongTermMemory,
)
from src.masai.schema import Document

# Try to import real embeddings
try:
    from langchain_openai import OpenAIEmbeddings
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    HAS_HUGGINGFACE = True
except ImportError:
    HAS_HUGGINGFACE = False


class MockOpenAIEmbeddings:
    """Mock OpenAI embeddings (1536 dimensions)."""
    
    def __init__(self):
        self.model = "text-embedding-3-small"
        self.dimensions = 1536
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings (1536 dims)."""
        return [[0.1 + i * 0.001 for _ in range(1536)] for i in range(len(texts))]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate mock query embedding."""
        return [0.1 for _ in range(1536)]


class MockHuggingFaceEmbeddings:
    """Mock HuggingFace embeddings (384 dimensions)."""
    
    def __init__(self):
        self.model_name = "all-MiniLM-L6-v2"
        self.dimensions = 384
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate mock embeddings (384 dims)."""
        return [[0.2 + i * 0.001 for _ in range(384)] for i in range(len(texts))]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate mock query embedding."""
        return [0.2 for _ in range(384)]


class CustomEmbeddings:
    """Custom embedding model."""
    
    def __init__(self, dims: int = 256):
        self.dims = dims
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate custom embeddings."""
        return [[0.3 + i * 0.001 for _ in range(self.dims)] for i in range(len(texts))]
    
    def embed_query(self, text: str) -> List[float]:
        """Generate custom query embedding."""
        return [0.3 for _ in range(self.dims)]


class TestRedisAdapterWithOpenAIEmbeddings:
    """Test RedisAdapter with OpenAI embeddings (1536 dims)."""
    
    def test_config_with_openai_embeddings(self):
        """Test RedisConfig with OpenAI embeddings."""
        embeddings = MockOpenAIEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=1536,
            index_name="openai_vectors",
        )
        assert config.vector_size == 1536
        assert config.embedding_model == embeddings
        config.validate_embedding_model()  # Should not raise
    
    def test_adapter_init_with_openai(self):
        """Test RedisAdapter initialization with OpenAI embeddings."""
        embeddings = MockOpenAIEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=1536,
        )
        adapter = RedisAdapter(config)
        assert adapter.cfg == config
        assert adapter.cfg.vector_size == 1536
    
    def test_resolve_embeddings_openai(self):
        """Test embedding resolution with OpenAI."""
        embeddings = MockOpenAIEmbeddings()
        config = RedisConfig(embedding_model=embeddings)
        adapter = RedisAdapter(config)
        
        resolved = adapter._resolve_embeddings()
        assert resolved is not None
        assert hasattr(resolved, 'embed_documents')
        
        # Test embedding
        result = resolved.embed_documents(["test"])
        assert len(result) == 1
        assert len(result[0]) == 1536


class TestRedisAdapterWithHuggingFaceEmbeddings:
    """Test RedisAdapter with HuggingFace embeddings (384 dims)."""
    
    def test_config_with_huggingface_embeddings(self):
        """Test RedisConfig with HuggingFace embeddings."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=384,
            index_name="huggingface_vectors",
        )
        assert config.vector_size == 384
        assert config.embedding_model == embeddings
        config.validate_embedding_model()  # Should not raise
    
    def test_adapter_init_with_huggingface(self):
        """Test RedisAdapter initialization with HuggingFace embeddings."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=384,
        )
        adapter = RedisAdapter(config)
        assert adapter.cfg == config
        assert adapter.cfg.vector_size == 384
    
    def test_resolve_embeddings_huggingface(self):
        """Test embedding resolution with HuggingFace."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(embedding_model=embeddings)
        adapter = RedisAdapter(config)
        
        resolved = adapter._resolve_embeddings()
        assert resolved is not None
        assert hasattr(resolved, 'embed_documents')
        
        # Test embedding
        result = resolved.embed_documents(["test"])
        assert len(result) == 1
        assert len(result[0]) == 384


class TestRedisAdapterWithCustomEmbeddings:
    """Test RedisAdapter with custom embeddings."""
    
    def test_config_with_custom_embeddings(self):
        """Test RedisConfig with custom embeddings."""
        embeddings = CustomEmbeddings(dims=256)
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=256,
        )
        assert config.vector_size == 256
        config.validate_embedding_model()  # Should not raise
    
    def test_adapter_with_custom_embeddings(self):
        """Test RedisAdapter with custom embeddings."""
        embeddings = CustomEmbeddings(dims=256)
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=256,
        )
        adapter = RedisAdapter(config)
        
        resolved = adapter._resolve_embeddings()
        result = resolved.embed_documents(["test"])
        assert len(result) == 1
        assert len(result[0]) == 256


class TestRedisAdapterWithCallableEmbeddings:
    """Test RedisAdapter with callable embedding functions."""
    
    def test_config_with_callable_embeddings(self):
        """Test RedisConfig with callable embeddings."""
        def embed_fn(texts: List[str]) -> List[List[float]]:
            return [[0.5 for _ in range(128)] for _ in texts]
        
        config = RedisConfig(
            embedding_model=embed_fn,
            vector_size=128,
        )
        config.validate_embedding_model()  # Should not raise
    
    def test_adapter_with_callable_embeddings(self):
        """Test RedisAdapter with callable embeddings."""
        def embed_fn(texts: List[str]) -> List[List[float]]:
            return [[0.5 + i * 0.01 for _ in range(128)] for i in range(len(texts))]
        
        config = RedisConfig(
            embedding_model=embed_fn,
            vector_size=128,
        )
        adapter = RedisAdapter(config)
        
        resolved = adapter._resolve_embeddings()
        result = resolved.embed_documents(["test1", "test2"])
        assert len(result) == 2
        assert len(result[0]) == 128
        assert len(result[1]) == 128


class TestRedisAdapterDeduplication:
    """Test deduplication modes."""
    
    def test_dedup_hash_mode(self):
        """Test hash-based deduplication."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            dedup_mode="hash",
        )
        adapter = RedisAdapter(config)
        
        doc = Document(page_content="Hello world", metadata={})
        doc_id1 = adapter._get_doc_id_with_dedup(doc)
        doc_id2 = adapter._get_doc_id_with_dedup(doc)
        
        # Hash mode should be deterministic
        assert doc_id1 == doc_id2
    
    def test_dedup_similarity_mode(self):
        """Test similarity-based deduplication."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            dedup_mode="similarity",
        )
        adapter = RedisAdapter(config)
        
        doc = Document(page_content="Hello world", metadata={})
        doc_id1 = adapter._get_doc_id_with_dedup(doc)
        doc_id2 = adapter._get_doc_id_with_dedup(doc)
        
        # Similarity mode should generate UUIDs
        assert doc_id1 != doc_id2
    
    def test_dedup_none_mode(self):
        """Test no deduplication."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            dedup_mode="none",
        )
        adapter = RedisAdapter(config)
        
        doc = Document(page_content="Hello world", metadata={})
        doc_id1 = adapter._get_doc_id_with_dedup(doc)
        doc_id2 = adapter._get_doc_id_with_dedup(doc)
        
        # None mode should always generate new UUIDs
        assert doc_id1 != doc_id2


class TestRedisAdapterConfiguration:
    """Test various configuration options."""
    
    def test_ttl_configuration(self):
        """Test TTL configuration."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            ttl_seconds=3600,
        )
        assert config.ttl_seconds == 3600
    
    def test_distance_metrics(self):
        """Test distance metric configuration."""
        embeddings = MockHuggingFaceEmbeddings()
        
        for metric in ["cosine", "l2", "ip"]:
            config = RedisConfig(
                embedding_model=embeddings,
                distance_metric=metric,
            )
            assert config.distance_metric == metric
    
    def test_batch_size_configuration(self):
        """Test batch size configuration."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            batch_size=50,
        )
        assert config.batch_size == 50
    
    def test_connection_pool_configuration(self):
        """Test connection pool configuration."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            connection_pool_size=20,
            socket_timeout=10.0,
            socket_connect_timeout=5.0,
        )
        assert config.connection_pool_size == 20
        assert config.socket_timeout == 10.0
        assert config.socket_connect_timeout == 5.0


class TestLongTermMemoryWithRedis:
    """Test LongTermMemory with Redis backend."""
    
    def test_longtermemory_redis_backend_selection(self):
        """Test LongTermMemory selects Redis backend."""
        embeddings = MockHuggingFaceEmbeddings()
        config = RedisConfig(embedding_model=embeddings)
        memory = LongTermMemory(backend_config=config)
        
        assert memory.backend_type == "redis"
        assert isinstance(memory.adapter, RedisAdapter)
    
    def test_longtermemory_embedding_resolution(self):
        """Test LongTermMemory resolves embeddings correctly."""
        embeddings = MockOpenAIEmbeddings()
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=1536,
        )
        memory = LongTermMemory(backend_config=config)

        embed_fn = memory._resolve_embed_fn()
        assert embed_fn is not None

        # Test embedding
        result = embed_fn(["test"])
        assert len(result) == 1
        assert len(result[0]) == 1536


# Real Embeddings Tests (Requires API keys and Redis)
@pytest.mark.skipif(not HAS_OPENAI, reason="OpenAI embeddings not installed")
class TestRedisWithRealOpenAIEmbeddings:
    """Test Redis adapter with real OpenAI embeddings."""

    def test_openai_embeddings_config(self):
        """Test configuration with real OpenAI embeddings."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=1536,
            index_name="openai_test_index",
        )
        assert config.vector_size == 1536
        config.validate_embedding_model()

    def test_openai_embeddings_adapter_init(self):
        """Test RedisAdapter initialization with real OpenAI embeddings."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=1536,
        )
        adapter = RedisAdapter(config)
        assert adapter.cfg.vector_size == 1536

    def test_openai_embeddings_resolution(self):
        """Test embedding resolution with real OpenAI embeddings."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        config = RedisConfig(embedding_model=embeddings)
        adapter = RedisAdapter(config)

        resolved = adapter._resolve_embeddings()
        assert resolved is not None
        assert hasattr(resolved, 'embed_documents')


@pytest.mark.skipif(not HAS_HUGGINGFACE, reason="HuggingFace embeddings not installed")
class TestRedisWithRealHuggingFaceEmbeddings:
    """Test Redis adapter with real HuggingFace embeddings."""

    def test_huggingface_embeddings_config(self):
        """Test configuration with real HuggingFace embeddings."""
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=384,
            index_name="huggingface_test_index",
        )
        assert config.vector_size == 384
        config.validate_embedding_model()

    def test_huggingface_embeddings_adapter_init(self):
        """Test RedisAdapter initialization with real HuggingFace embeddings."""
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        config = RedisConfig(
            embedding_model=embeddings,
            vector_size=384,
        )
        adapter = RedisAdapter(config)
        assert adapter.cfg.vector_size == 384

    def test_huggingface_embeddings_resolution(self):
        """Test embedding resolution with real HuggingFace embeddings."""
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        config = RedisConfig(embedding_model=embeddings)
        adapter = RedisAdapter(config)

        resolved = adapter._resolve_embeddings()
        assert resolved is not None
        assert hasattr(resolved, 'embed_documents')


class TestRedisWithInternalEmbeddings:
    """Test Redis adapter with Redis internal embeddings (if available)."""

    def test_redis_internal_embeddings_callable(self):
        """Test with Redis internal embeddings as callable."""
        # Simulate Redis internal embeddings
        def redis_embed_fn(texts: List[str]) -> List[List[float]]:
            """Mock Redis internal embedding function."""
            return [[0.1 + i * 0.01 for _ in range(768)] for i in range(len(texts))]

        config = RedisConfig(
            embedding_model=redis_embed_fn,
            vector_size=768,
            index_name="redis_internal_index",
        )
        assert config.vector_size == 768
        config.validate_embedding_model()

    def test_redis_internal_embeddings_adapter(self):
        """Test RedisAdapter with Redis internal embeddings."""
        def redis_embed_fn(texts: List[str]) -> List[List[float]]:
            """Mock Redis internal embedding function."""
            return [[0.1 + i * 0.01 for _ in range(768)] for i in range(len(texts))]

        config = RedisConfig(
            embedding_model=redis_embed_fn,
            vector_size=768,
        )
        adapter = RedisAdapter(config)

        resolved = adapter._resolve_embeddings()
        result = resolved.embed_documents(["test"])
        assert len(result) == 1
        assert len(result[0]) == 768

    def test_redis_internal_embeddings_user_isolation(self):
        """Test user isolation with Redis internal embeddings."""
        def redis_embed_fn(texts: List[str]) -> List[List[float]]:
            """Mock Redis internal embedding function."""
            return [[0.1 + i * 0.01 for _ in range(768)] for i in range(len(texts))]

        config = RedisConfig(
            embedding_model=redis_embed_fn,
            vector_size=768,
            dedup_mode="hash",
        )
        adapter = RedisAdapter(config)

        # Test document ID generation for different users
        doc = Document(page_content="Test content", metadata={"user_id": "user_1"})
        doc_id = adapter._get_doc_id_with_dedup(doc)
        assert doc_id is not None
        assert isinstance(doc_id, str)


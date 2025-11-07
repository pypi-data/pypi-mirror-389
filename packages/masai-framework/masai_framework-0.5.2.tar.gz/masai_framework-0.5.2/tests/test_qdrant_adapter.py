import os
import sys
import uuid
import asyncio
from typing import List

# Ensure 'src' is on path for local imports
sys.path.insert(0, os.path.abspath("src"))

from dotenv import load_dotenv

try:
    from masai.Memory.LongTermMemory import QdrantConfig, QdrantAdapter  # type: ignore
    _IMPORT_OK = True
except Exception as e:
    QdrantConfig = None  # type: ignore
    QdrantAdapter = None  # type: ignore
    _IMPORT_OK = False


def _toy_embed(texts: List[str]) -> List[List[float]]:
    """
    Free, dependency-less toy embedder for tests.
    Maps text deterministically to a 32-dim vector via hashed tokens.
    """
    import numpy as np

    dim = 32
    vecs = []
    for t in texts:
        v = np.zeros(dim, dtype=float)
        # simple token hash
        for tok in str(t).lower().split():
            h = abs(hash(tok)) % dim
            v[h] += 1.0
        # L2 normalize; avoid div by zero
        n = np.linalg.norm(v)
        if n > 0:
            v = v / n
        vecs.append(v.tolist())
    return vecs


def _get_cfg() -> QdrantConfig:  # type: ignore
    load_dotenv()
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY", None)
    coll = f"masai_memories_test_{uuid.uuid4().hex[:8]}"
    return QdrantConfig(url=url, api_key=api_key, collection_name=coll, vector_size=32, distance="cosine")


async def _prepare_adapter(cfg):
    adapter = QdrantAdapter(cfg)
    await adapter.ensure_collection()
    return adapter


def test_qdrant_upsert_and_search_user_filter():
    if not _IMPORT_OK:
        print("[SKIP] qdrant-client not installed or import failed")
        return

    async def _run():
        cfg = _get_cfg()
        adapter = await _prepare_adapter(cfg)

        user_a = "user_a"
        user_b = "user_b"

        docs_a = [
            {"page_content": "Alice likes apples", "metadata": {"categories": ["food"]}},
            {"page_content": "Alice works in Berlin", "metadata": {"categories": ["work", "location"]}},
        ]
        docs_b = [
            {"page_content": "Bob likes bananas", "metadata": {"categories": ["food"]}},
        ]

        await adapter.upsert_documents(user_id=user_a, documents=docs_a, embed_fn=_toy_embed)
        await adapter.upsert_documents(user_id=user_b, documents=docs_b, embed_fn=_toy_embed)

        # user filter: query should only return user_a docs for user_a
        res_a = await adapter.search(user_id=user_a, query="Alice", k=5, categories=None, embed_fn=_toy_embed)
        assert any("Alice" in d.page_content for d in res_a)
        assert all((d.metadata.get("user_id") == user_a or d.metadata.get("user_id") is None) for d in res_a)

        # categories filter: only docs with 'food'
        res_food = await adapter.search(user_id=user_a, query="likes", k=5, categories=["food"], embed_fn=_toy_embed)
        assert any("apples" in d.page_content for d in res_food)

        # cleanup
        await adapter.client.delete_collection(collection_name=cfg.collection_name)

    asyncio.run(_run())


def test_qdrant_delete_by_doc_id():
    if not _IMPORT_OK:
        print("[SKIP] qdrant-client not installed or import failed")
        return

    async def _run():
        cfg = _get_cfg()
        adapter = await _prepare_adapter(cfg)

        user_id = "user_z"
        doc = {"page_content": "Zoe travels often", "metadata": {"categories": ["travel"]}}
        await adapter.upsert_documents(user_id=user_id, documents=[doc], embed_fn=_toy_embed)

        # fetch the inserted point id using raw client search
        query_vec = _toy_embed(["Zoe travels"])[0]
        from qdrant_client.http import models as qmodels
        result = await adapter.client.search(
            collection_name=cfg.collection_name,
            query_vector=query_vec,
            limit=1,
            query_filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id))]
            ),
        )
        assert result, "Expected at least one search result"
        point_id = result[0].id

        # delete using adapter API
        await adapter.delete_by_doc_id(user_id=user_id, doc_id=point_id)

        # verify it's gone (search again)
        from qdrant_client.http import models as qmodels
        result2 = await adapter.client.search(
            collection_name=cfg.collection_name,
            query_vector=query_vec,
            limit=1,
            query_filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key="user_id", match=qmodels.MatchValue(value=user_id))]
            ),
        )
        # Qdrant returns empty list if none
        assert not result2, "Expected no results after deletion"

        # cleanup
        await adapter.client.delete_collection(collection_name=cfg.collection_name)

    asyncio.run(_run())


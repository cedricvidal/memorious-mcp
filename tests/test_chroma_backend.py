import pytest
import uuid
from typing import Optional, Dict, Any

import backends.chroma_backend as cb


@pytest.mark.integration
def test_store_and_recall_exact():
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16)

    _id = backend.store("alpha", "value-alpha", metadata={"k": 1})
    assert isinstance(_id, str) and len(_id) > 0

    results = backend.recall("alpha", top_k=1)
    assert len(results) == 1
    res = results[0]
    assert res["id"] == _id
    assert res["document"] == "alpha"
    assert res["metadata"]["value"] == "value-alpha"

    # cleanup
    try:
        if hasattr(backend.client, "delete_collection"):
            backend.client.delete_collection(collection_name)
    except Exception:
        pass


@pytest.mark.integration
def test_forget_removes_items():
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16)

    id1 = backend.store("beta", "value-beta-1")
    id2 = backend.store("beta", "value-beta-2")

    results_all = backend.recall("beta", top_k=2)
    assert len(results_all) == 2

    # forget one
    deleted = backend.forget("beta", top_k=1)
    assert len(deleted) == 1

    # after deletion, one remains
    remaining = backend.recall("beta", top_k=2)
    assert len(remaining) == 1
    assert remaining[0]["id"] != deleted[0]

    # cleanup
    try:
        if hasattr(backend.client, "delete_collection"):
            backend.client.delete_collection(collection_name)
    except Exception:
        pass


@pytest.mark.integration
def test_forget_returns_empty_when_no_match():
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16)

    # nothing stored
    deleted = backend.forget("nonexistent", top_k=1)
    assert deleted == []

    # cleanup
    try:
        if hasattr(backend.client, "delete_collection"):
            backend.client.delete_collection(collection_name)
    except Exception:
        pass

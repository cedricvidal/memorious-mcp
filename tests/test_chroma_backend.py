import pytest
import uuid
from typing import Optional, Dict, Any

import backends.chroma_backend as cb


def test_store_and_recall_exact(tmp_path):
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16, persist_directory=str(tmp_path))

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
        backend.client.delete_collection(collection_name)
    except Exception:
        pass


def test_forget_removes_items(tmp_path):
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16, persist_directory=str(tmp_path))

    # Use distinct keys because keys are used as persistent IDs
    key1 = "beta-1"
    key2 = "beta-2"
    id1 = backend.store(key1, "value-beta-1")
    id2 = backend.store(key2, "value-beta-2")

    # Ensure stored ids are the keys
    assert id1 == key1
    assert id2 == key2

    # forget the first key
    deleted = backend.forget(key1, top_k=1)
    # the delete should include the first id
    assert any(d == id1 for d in deleted)

    # after deletion, key1 should no longer be returned by recall
    remaining = backend.recall(key1, top_k=2)
    assert all(r["id"] != id1 for r in remaining)

    # cleanup
    try:
        backend.client.delete_collection(collection_name)
    except Exception:
        pass


def test_forget_returns_empty_when_no_match(tmp_path):
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16, persist_directory=str(tmp_path))

    # nothing stored
    deleted = backend.forget("nonexistent", top_k=1)
    assert deleted == []

    # cleanup
    try:
        backend.client.delete_collection(collection_name)
    except Exception:
        pass

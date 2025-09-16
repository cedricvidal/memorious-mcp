import pytest
import uuid
import yaml
from pathlib import Path
from typing import Optional, Dict, Any

from memorious_mcp.backends import chroma_backend as cb


def test_store_and_recall_exact(tmp_path):
    collection_name = f"test_collection_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=16, persist_directory=str(tmp_path))

    _id = backend.store("alpha", "value-alpha", metadata={"k": 1})
    assert isinstance(_id, str) and len(_id) > 0

    results = backend.recall("alpha", top_k=1)
    assert len(results) == 1
    res = results[0]
    assert res["id"] == _id
    assert res["key"] == "alpha"
    assert res["value"] == "value-alpha"

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


# Load variations for parameterized tests
_VARIATIONS_PATH = Path(__file__).parent / "test_variations.yaml"
_VARIATIONS = []
if _VARIATIONS_PATH.exists():
    with _VARIATIONS_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        for mem in data.get("memories", []):
            _VARIATIONS.append((mem["key"], mem["value"], mem.get("queries", []), mem.get("negatives", [])))


@pytest.mark.parametrize("key,value,queries,negatives", _VARIATIONS)
def test_variations_recall(tmp_path, key, value, queries, negatives):
    """For each sample in test_variations.yaml, store the memory and ensure queries recall it."""
    collection_name = f"test_collection_var_{uuid.uuid4().hex}"
    backend = cb.ChromaMemoryBackend(collection_name=collection_name, embedding_dim=64, persist_directory=str(tmp_path))

    # store the sample
    backend.store(key, value)

    # store negative examples as distinct memories so they exist in the index
    negative_values = {}
    for n in negatives:
        neg_val = f"NEGATIVE::{uuid.uuid4().hex}"
        negative_values[n] = neg_val
        backend.store(n, neg_val)

    # sanity-check: each negative query should retrieve its own negative value
    for n, neg_val in negative_values.items():
        neg_results = backend.recall(n, top_k=1)
        if len(neg_results) > 0:
            assert neg_results[0]["value"] == neg_val

    # ensure negative examples do not return the stored value
    for n in negatives:
        neg_results = backend.recall(n, top_k=1)
        # either no results or top result must not be the stored value
        if len(neg_results) > 0:
            assert neg_results[0]["value"] != value

    # ensure each query returns the stored value as top-1
    for q in queries:
        results = backend.recall(q, top_k=1)
        assert len(results) >= 1
        assert results[0]["value"] == value

    # cleanup
    try:
        backend.client.delete_collection(collection_name)
    except Exception:
        pass

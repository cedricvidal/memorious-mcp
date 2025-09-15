import hashlib
import math
import uuid
import chromadb
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from backends.memory_backend import MemoryBackend


class ChromaMemoryBackend(MemoryBackend):
    """
    Wraps a ChromaDB collection and provides store/recall/forget semantics.

    - store(key, value, metadata): store a record whose indexed document is the `key` (so similarity
      queries on the key find matches). The actual `value` is stored inside metadata under 'value'.
    - recall(key, top_k): return the nearest stored items to the provided key (by cosine similarity).
    - forget(key, top_k, threshold): delete nearest items to the provided key.
    """

    def __init__(self, collection_name: str = "memories", embedding_dim: int = 128):
        self.collection_name = collection_name
        self.embedding = LocalEmbedding(dim=embedding_dim)
        self.client = chromadb.Client()
        # Try to get existing collection, otherwise create one
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # create_collection accepts embedding_function with embed_documents/embed_query
            self.collection = self.client.create_collection(name=self.collection_name, embedding_function=self.embedding)

    def store(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        _id = uuid.uuid4().hex
        meta = dict(metadata) if metadata else {}
        meta.setdefault("key", key)
        meta["value"] = value
        # We index by the key (documents are what get embedded/indexed)
        self.collection.add(ids=[_id], documents=[key], metadatas=[meta])
        return _id

    def recall(self, key: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # Query by embedding of key to get nearest documents
        # Chromadb returns lists for each field
        result = self.collection.query(query_texts=[key], n_results=top_k, include=["metadatas", "documents", "distances", "ids"])  # type: ignore[arg-type]
        items = []
        # result fields are lists of lists because we queried with a batch of size 1
        for idx in range(len(result.get("ids", [[]])[0])):
            items.append(
                {
                    "id": result.get("ids", [[None]])[0][idx],
                    "document": result.get("documents", [[None]])[0][idx],
                    "metadata": result.get("metadatas", [[None]])[0][idx],
                    "distance": result.get("distances", [[None]])[0][idx],
                }
            )
        return items

    def forget(self, key: str, top_k: int = 3) -> List[str]:
        results = self.recall(key, top_k=top_k)
        ids_to_delete = [r["id"] for r in results if r.get("id")]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
        return ids_to_delete


class LocalEmbedding:
    """
    Deterministic, dependency-free embedding function for small demos/tests.
    Implements the minimal interface expected by ChromaDB: embed_documents(list[str]) -> list[list[float]]
    and embed_query(str) -> list[float].

    This uses repeated SHA-256 hashing to produce a fixed-dimensional float vector.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def _hash_to_vector(self, text: str) -> List[float]:
        # Create a sufficiently long byte stream by hashing several times
        data = text.encode("utf-8")
        out = b""
        counter = 0
        # accumulate bytes until we have at least dim * 4 bytes
        while len(out) < self.dim * 4:
            h = hashlib.sha256(data + counter.to_bytes(4, "big")).digest()
            out += h
            counter += 1
        # convert to floats in range [-1,1]
        vec = []
        for i in range(self.dim):
            chunk = out[i * 4 : (i + 1) * 4]
            as_int = int.from_bytes(chunk, "big", signed=False)
            # normalize to [-1, 1]
            val = (as_int / (2**32 - 1)) * 2 - 1
            vec.append(val)
        # normalize to unit length for cosine-similarity
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._hash_to_vector(text)

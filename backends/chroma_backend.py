import hashlib
import math
import uuid
import chromadb
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from backends.memory_backend import MemoryBackend

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


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
        # Prefer ChromaDB's built-in DefaultEmbeddingFunction when available
        # instantiate default embedding function (no args typically required)
        self.embedding = DefaultEmbeddingFunction()

        self.client = chromadb.Client()
        # Try to get existing collection, otherwise create one
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # create_collection accepts embedding_function with embed_documents/embed_query
            if self.embedding is not None:
                self.collection = self.client.create_collection(name=self.collection_name, embedding_function=self.embedding)
            else:
                # let chromadb decide the default embedding function if none supplied
                self.collection = self.client.create_collection(name=self.collection_name)

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
        result = self.collection.query(query_texts=[key], n_results=top_k, include=["metadatas", "documents", "distances"])  # type: ignore[arg-type]
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

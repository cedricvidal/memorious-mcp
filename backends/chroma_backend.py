import hashlib
import math
import uuid
import chromadb
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from backends.memory_backend import MemoryBackend
from chromadb.config import Settings
from datetime import datetime, timezone

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


class ChromaMemoryBackend(MemoryBackend):
    """
    Wraps a ChromaDB collection and provides store/recall/forget semantics.

    - store(key, value, metadata): store a record whose indexed document is the `key` (so similarity
      queries on the key find matches). The actual `value` is stored inside metadata under 'value'.
    - recall(key, top_k): return the nearest stored items to the provided key (by cosine similarity).
    - forget(key, top_k, threshold): delete nearest items to the provided key.
    """

    def __init__(
        self, collection_name: str = "memories", embedding_dim: int = 128, persist_directory: Optional[str] = None
    ):
        self.collection_name = collection_name
        # Always enable persistence; normalize falsy values to the default path
        if not persist_directory:
            persist_directory = "./.chroma_db"

        # Prefer ChromaDB's built-in DefaultEmbeddingFunction when available
        # instantiate default embedding function (no args typically required)
        self.embedding = DefaultEmbeddingFunction()

        # Create a persistent client unconditionally (persistence cannot be deactivated)
        self.client = chromadb.PersistentClient(path=persist_directory)

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
        # Use the provided key as the persistent identifier for the memory
        _id = str(key)
        meta = dict(metadata) if metadata else {}
        meta["key"] = key
        meta["value"] = value
        # Add a timezone-aware UTC timestamp for when this memory was stored
        meta["timestamp"] = datetime.now(timezone.utc).isoformat()
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
            md = result.get("metadatas", [[None]])[0][idx]
            ts = None
            val = None
            if isinstance(md, dict):
                ts = md.get("timestamp")
                val = md.get("value")
            items.append(
                {
                    "id": result.get("ids", [[None]])[0][idx],
                    "key": result.get("documents", [[None]])[0][idx],
                    "value": val,
                    "distance": result.get("distances", [[None]])[0][idx],
                    "timestamp": ts,
                }
            )
        return items

    def forget(self, key: str, top_k: int = 3) -> List[str]:
        results = self.recall(key, top_k=top_k)
        ids_to_delete = [r["id"] for r in results if r.get("id")]
        if ids_to_delete:
            self.collection.delete(ids=ids_to_delete)
        return ids_to_delete

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class MemoryBackend(ABC):
    """Abstract interface for memory backends.

    Implementations should provide a simple key-based memory store with
    vector-similarity recall semantics.
    """

    @abstractmethod
    def store(self, key: str, value: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a key/value with optional metadata and return a unique id."""
        raise NotImplementedError

    @abstractmethod
    def recall(self, key: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Recall nearest items for a given key."""
        raise NotImplementedError

    @abstractmethod
    def forget(self, key: str, top_k: int = 3) -> List[str]:
        """Delete nearest items for a given key and return deleted ids."""
        raise NotImplementedError

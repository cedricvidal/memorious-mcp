import argparse
import hashlib
import math
import uuid
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP, Context

from backends.chroma_backend import ChromaMemoryBackend


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


def build_mcp(collection_name: str = "memories") -> FastMCP:
    """
    Build a FastMCP server instance and register store/recall/forget tools.
    """
    mcp = FastMCP("MemoryMCP")
    # attach a MemoryStore instance to the server for tool implementations
    mcp.memory = ChromaMemoryBackend(collection_name=collection_name)

    @mcp.tool
    async def store(key: str, value: str, metadata: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None):
        """Store a (key, value) pair. Key is indexed by vector similarity; value is stored in metadata."""
        _id = mcp.memory.store(key=key, value=value, metadata=metadata)
        if ctx:
            await ctx.info(f"Stored memory id={_id} key={key}")
        return {"id": _id}

    @mcp.tool
    async def recall(key: str, top_k: int = 3, ctx: Optional[Context] = None):
        """Recall nearest memories to the provided key."""
        items = mcp.memory.recall(key=key, top_k=top_k)
        if ctx:
            await ctx.info(f"Recalled {len(items)} items for key={key}")
        return {"results": items}

    @mcp.tool
    async def forget(key: str, top_k: int = 3, ctx: Optional[Context] = None):
        """Forget (delete) nearest memories to the provided key."""
        deleted = mcp.memory.forget(key=key, top_k=top_k)
        if ctx:
            await ctx.info(f"Deleted {len(deleted)} memories for key={key}")
        return {"deleted_ids": deleted}

    return mcp


def main():
    parser = argparse.ArgumentParser("mcp-memory-stdio-server")
    parser.add_argument("--collection", default="memories", help="ChromaDB collection name to use")
    args = parser.parse_args()

    mcp = build_mcp(collection_name=args.collection)

    print("Starting FastMCP stdio MCP server using collection '%s'" % args.collection)
    # Default transport is STDIO for FastMCP; run the server and accept MCP stdio calls
    mcp.run()


if __name__ == "__main__":
    main()

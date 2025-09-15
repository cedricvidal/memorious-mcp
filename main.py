import argparse
import hashlib
import math
import uuid
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP, Context

from backends.chroma_backend import ChromaMemoryBackend


def build_mcp(collection_name: str = "memories") -> FastMCP:
    """
    Build a FastMCP server instance and register store/recall/forget tools.
    """
    mcp = FastMCP("MemoryMCP")
    # attach a MemoryStore instance to the server for tool implementations
    memory = ChromaMemoryBackend(collection_name=collection_name)

    @mcp.tool
    async def store(key: str, value: str, metadata: Optional[Dict[str, Any]] = None, ctx: Optional[Context] = None):
        """Store a (key, value) pair. Key is indexed by vector similarity; value is stored in metadata."""
        _id = memory.store(key=key, value=value, metadata=metadata)
        if ctx:
            await ctx.info(f"Stored memory id={_id} key={key}")
        return {"id": _id}

    @mcp.tool
    async def recall(key: str, top_k: int = 3, ctx: Optional[Context] = None):
        """Recall nearest memories to the provided key."""
        items = memory.recall(key=key, top_k=top_k)
        if ctx:
            await ctx.info(f"Recalled {len(items)} items for key={key}")
        distances = [it.get("distance") for it in items]
        return {"results": items, "distances": distances}

    @mcp.tool
    async def forget(key: str, top_k: int = 3, ctx: Optional[Context] = None):
        """Forget (delete) nearest memories to the provided key."""
        deleted = memory.forget(key=key, top_k=top_k)
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

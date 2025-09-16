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
    async def store(key: str, value: str, ctx: Optional[Context] = None):
        """Store a user's fact, piece of information, or preference for later recall.

        This tool SHOULD be called by the LLM whenever the user states a fact, personal
        detail, or stable preference that the assistant is expected to remember
        (for example: "I like jazz", "I live in Paris", "My favorite editor is VS Code").

        Guidelines for the LLM:
        - Call this tool when the user expresses facts, identity details, or explicit
          preferences the assistant may need later.
        - Use `key` as a short, concise descriptor suitable for embedding-based similarity
          searches (e.g. "likes_jazz", "lives_in_paris").
        - Use `value` for the full text of the fact or preference to be stored and returned
          on recall.

        Privacy: avoid storing highly sensitive data (passwords, social security numbers,
        bank details) unless the user explicitly requests secure storage and consents.
        """
        _id = memory.store(key=key, value=value)
        if ctx:
            await ctx.info(f"Stored memory id={_id} key={key}")
        return {"id": _id}

    @mcp.tool
    async def recall(key: str, top_k: int = 3, ctx: Optional[Context] = None):
        """Retrieve stored memories relevant to a query key.

        This tool SHOULD be called by the LLM when it needs to fetch previously stored
        facts, personal details, or preferences to inform a response or provide
        personalized behavior (for example: to recall a user's favorite cuisine
        before making restaurant suggestions).

        Parameters:
        - key: concise query text used for embedding-based similarity search
               (e.g. "likes_jazz", "lives_in_paris").
        - top_k: maximum number of nearest memories to return.

        Returns a dict with `results` (memory items including stored value).
        If nothing matches, `results` is empty.
        """
        items = memory.recall(key=key, top_k=top_k)
        if ctx:
            await ctx.info(f"Recalled {len(items)} items for key={key}")
        return {"results": items}

    @mcp.tool
    async def forget(key: str, top_k: int = 3, ctx: Optional[Context] = None):
        """Delete stored memories that match a query key.

        This tool SHOULD be called by the LLM when the user explicitly requests that
        certain stored information be forgotten or removed (for example: "forget
        that I live in Paris") or when the assistant decides a memory must be
        purged because it is incorrect or sensitive.

        Parameters:
        - key: concise query text used to find candidate memories to delete.
        - top_k: number of nearest matches to consider for deletion.

        Behavior:
        - Deletion is irreversible; the LLM should confirm with the user when
          intent is ambiguous before invoking this tool.
        - The tool returns `deleted_ids` for the memories that were removed.
        """
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

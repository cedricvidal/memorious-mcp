import argparse
import hashlib
import math
import uuid
from typing import List, Dict, Any, Optional

from fastmcp import FastMCP, Context

from .backends.chroma_backend import ChromaMemoryBackend


def build_mcp(collection_name: str = "memories") -> FastMCP:
    """
    Build a FastMCP server instance and register store/recall/forget tools.
    """
    mcp = FastMCP("MemoriousMCP")
    # attach a MemoryStore instance to the server for tool implementations
    memory = ChromaMemoryBackend(collection_name=collection_name)

    @mcp.tool
    async def store(key: str, value: str, ctx: Optional[Context] = None):
        """Store a user's fact, piece of information, or preference for later recall.

        IMPORTANT: `key` MUST be short, canonical, and optimized for
        embedding/vector similarity lookups. Prefer 1–5 words separated by spaces
        (for example: "likes jazz", "pref cuisine italian", "lives in paris").
        Do NOT use long sentences or paragraphs as keys — put long text into
        `value` instead.

        This tool SHOULD be called by the LLM whenever the user states a fact,
        personal detail, or stable preference that the assistant is expected to
        remember.

        Guidelines for the LLM:
        - Call this tool for user-expressed facts, identity details, or explicit
          preferences that will be useful later.
        - Use `key` as a short, consistent, space-separated descriptor across
          related memories to improve retrieval quality (canonicalize synonyms
          where possible).
        - Use `value` for the full text of the fact or preference to be stored
          and returned on recall; include any extra context inside `value`.

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

        IMPORTANT: To get reliable results the LLM MUST query with the same short,
        canonical, embedding-optimized keys used at store time. Keys should be
        compact (1–5 words, space-separated) and represent the core concept — avoid
        long descriptive queries. If the current user utterance is verbose, the
        LLM should first map or canonicalize it to an appropriate short key before
        calling this tool (for example map "I really like listening to jazz music"
        -> "likes jazz").

        This tool SHOULD be called by the LLM when it needs to fetch previously stored
        facts, personal details, or preferences to inform a response or provide
        personalized behavior (for example: to recall a user's favorite cuisine
        before making restaurant suggestions).

        Parameters:
        - key: concise, embedding-friendly, space-separated query text used for
               similarity search.
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

        IMPORTANT: Deletion operates on short, canonical keys. The LLM MUST issue
        forget calls using the same concise, embedding-optimized, space-separated
        key style used to create memories (otherwise relevant memories may not be
        found). Prefer 1–5 words separated by spaces when requesting deletions.

        This tool SHOULD be called by the LLM when the user explicitly requests that
        certain stored information be forgotten or removed (for example: "forget
        that I live in Paris") or when the assistant decides a memory must be
        purged because it is incorrect or sensitive.

        Parameters:
        - key: concise, canonical, space-separated query text used to find candidate memories to delete.
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
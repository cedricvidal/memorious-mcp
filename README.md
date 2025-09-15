# memorious-mcp

Memorious-MCP is a minimal Model Context Protocol (MCP) server that provides a persistent key-value memory store with vector-similarity lookup using ChromaDB.

Features
- FastMCP-based MCP stdio server exposing three tools: `store`, `recall`, and `forget`.
- ChromaDB backend (`ChromaMemoryBackend`) persisting data on disk using Chroma's PersistentClient.
- Tests (integration) that exercise store/recall/forget behavior.

Getting started

1. Install (recommended in a virtual environment):

```bash
pip install .[dev]
```

2. Run the server (stdio transport, suitable for local/CLI integrations):

```bash
uv run main.py --collection memories
```

3. Call tools using an MCP client (FastMCP client or a compatible MCP client) over stdio.

Example tool signatures
- store(key: str, value: str, metadata: Optional[dict]) -> {"id": str}
- recall(key: str, top_k: int = 3) -> {"results": [...], "distances": [...]} where each result includes id, key, value, distance, timestamp
- forget(key: str, top_k: int = 3) -> {"deleted_ids": [...]}

Testing

Run tests with:

```bash
pytest
```

Notes

- By default memory persistence is enabled and stored under `./.chroma_db`. You can override `persist_directory` when creating `ChromaMemoryBackend` in code.
- The backend uses Chroma's default embedding function when available.

Contributing

Contributions are welcome. Open a PR with tests.

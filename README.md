# memorious-mcp

Memorious-MCP is a minimal Model Context Protocol (MCP) server that provides a persistent key-value memory store with vector-similarity lookup using ChromaDB.

## Features
- FastMCP-based MCP stdio server exposing three tools: `store`, `recall`, and `forget`.
- ChromaDB backend (`ChromaMemoryBackend`) persisting data on disk using Chroma's PersistentClient.
- Tests (integration) that exercise store/recall/forget behavior.
- Standard Python package layout for easy installation and distribution.

## Getting Started

1. Install the package (recommended in a virtual environment):

```bash
# Install in development mode
uv sync

# Or install from source
pip install .
```

2. Run the server (stdio transport, suitable for local/CLI integrations):

```bash
# Using uv
uv run memorious-mcp --collection memories

# Or if installed globally
memorious-mcp --collection memories
```

3. Call tools using an MCP client (FastMCP client or a compatible MCP client) over stdio.

## Example Tool Signatures
- `store(key: str, value: str) -> {"id": str}`
- `recall(key: str, top_k: int = 3) -> {"results": [...]}` where each result includes id, key, value, distance, timestamp
- `forget(key: str, top_k: int = 3) -> {"deleted_ids": [...]}`

## Testing

Run tests with:

```bash
# Using uv
uv run python -m pytest tests/ -v

# Or if pytest is available globally
pytest tests/ -v
```

## Package Structure

The project follows the standard Python package layout:

```
memorious-mcp/
├── src/
│   └── memorious_mcp/
│       ├── __init__.py
│       ├── main.py                 # MCP server entry point
│       └── backends/
│           ├── __init__.py
│           ├── memory_backend.py   # Abstract base class
│           └── chroma_backend.py   # ChromaDB implementation
├── tests/
│   └── test_chroma_backend.py      # Integration tests
├── pyproject.toml                  # Package configuration
└── README.md
```

## Notes

- By default memory persistence is enabled and stored under `./.memorious`. You can override `persist_directory` when creating `ChromaMemoryBackend` in code.
- The backend uses Chroma's default embedding function when available.
- The package is configured with a console script entry point for easy command-line usage.

## Contributing

Contributions are welcome. Open a PR with tests.

# memorious-mcp

<div align="center">

![sd](doc/logo.jpg)
</div>

A **100% local & private** semantic memory MCP (Model Context Protocol) server for AI assistants. Built with ChromaDB for vector similarity search and [FastMCP 2](https://gofastmcp.com/). **Runs entirely locally** - no data ever leaves your machine.

## Overview

memorious-mcp provides AI assistants with long-term memory capabilities through three core operations: `store`, `recall`, and `forget`. It uses ChromaDB's vector database to enable semantic similarity search, allowing assistants to retrieve relevant memories even when the exact wording differs from the original storage. **All processing and storage happens locally on your machine** - no data ever leaves your machine, ensuring complete privacy and security.

## Key Features

- 🏠 **100% Local & Private**: All data processing and storage happens on your machine - nothing goes to the cloud
- 💾 **Persistent Memory**: Data persists across sessions using ChromaDB's disk-based storage
- 🔍 **Semantic Search**: Vector embeddings enable similarity-based memory retrieval
- ⚡ **Simple API**: Three intuitive tools for memory management
- 🚀 **FastMCP Integration**: Built on FastMCP for efficient MCP server implementation
- 🎯 **Canonical Key Design**: Optimized for short, embedding-friendly keys (1-5 words)
- 📂 **Folder Scoped Storage**: Per-project memory isolation.

## Why This Project Exists

🔍 **Gap in the MCP Ecosystem**: Despite the growing popularity of memory MCP servers, there wasn't an existing memory server that combines **both** semantic similarity search **and** complete file based folder scoped local storage. Most memory solutions either:
- ☁️ Require cloud services and external API calls (compromising privacy) for either embeddings or storage or both
- 🔤 Only support exact key-value matching (no semantic understanding)
- 📁 Don't support folder scoped local storage

## Use Cases

- **Personal Assistant Memory**: Remember user preferences, habits, and personal information
- **Context Preservation**: Maintain conversation context across sessions
- **Knowledge Management**: Store and retrieve project-specific information
- **Personalization**: Enable AI assistants to provide personalized responses based on stored preferences
- **Privacy-First AI**: Keep sensitive personal data local while still having persistent memory
- **Folder-Scoped AI Agents**: Perfect for **VS Code Copilot Chat Modes** and **Claude Code agents** with per-project memory isolation

## Installation

### For VS Code

Make sure you have [uv](https://docs.astral.sh/uv/) and its its `uvx` command installed first.

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Memorious_MCP-0098FF?style=flat-square&logo=visualstudiocode&logoColor=ffffff)](vscode:mcp/install?%7B%22name%22%3A%22memorious%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22memorious-mcp%22%5D%7D)

[![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Memorious_MCP-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=ffffff)](vscode-insiders:mcp/install?%7B%22name%22%3A%22memorious%22%2C%22type%22%3A%22stdio%22%2C%22command%22%3A%22uvx%22%2C%22args%22%3A%5B%22memorious-mcp%22%5D%7D)

### For most MCP clients

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "memorious": {
      "command": "uvx",
      "args": ["memorious-mcp"]
    }
  }
}
```

## Development / Local Installation

```
uv sync
```

For development/local installation:
```json
{
  "mcpServers": {
    "memorious": {
      "command": "uv",
      "args": ["run", "memorious-mcp"],
      "cwd": "/path/to/memorious-mcp"
    }
  }
}
```

## Tools

### `store`
Store facts, preferences, or information with short canonical keys optimized for vector similarity.

**Parameters:**
- `key` (string): Short, canonical key (1-5 words, space-separated)
- `value` (string): The actual information to store

### `recall`
Retrieve stored memories using semantic similarity search.

**Parameters:**
- `key` (string): Query key for similarity search
- `top_k` (int, default: 3): Maximum number of results to return

### `forget`
Delete memories matching a query key.

**Parameters:**
- `key` (string): Query key to find memories to delete
- `top_k` (int, default: 3): Number of nearest matches to consider

## Claude CLI Configuration

To add memorious-mcp to Claude CLI, use the following commands:

```bash
# Add the MCP server using uvx (recommended)
claude mcp add memorious-mcp uvx memorious-mcp

# Alternative: for development/local installation
claude mcp add memorious-mcp uv run memorious-mcp --cwd /path/to/memorious-mcp
```

You can then list your configured MCP servers:
```bash
claude mcp list
```

And remove the server if needed:
```bash
claude mcp remove memorious-mcp
```

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

## Technical Details

- **Backend**: ChromaDB with persistent disk storage
- **Embeddings**: Uses ChromaDB's default embedding function (local processing)
- **Storage Location**: `./.memorious` directory (configurable)
- **Python Version**: Requires Python ≥3.12
- **License**: MIT
- **Privacy**: No network requests, no cloud dependencies, all data stays local

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

The server is designed for local/CLI integrations using stdio transport, making it suitable for personal AI assistants and development workflows where privacy and data security are paramount.

## Limitations

⚠️ **Important Security Considerations**

While your data is **100% safe and private** because it never leaves your local machine, you should still exercise caution about what you store:

- **Data is stored unencrypted**: All stored data is persisted to disk in unencrypted format in the `.memorious` directory
- **Avoid storing secrets**: Do NOT store passwords, API keys, private keys, personal identification numbers, financial information, or any other sensitive credentials
- **Local file access**: Anyone with access to your machine and the `.memorious` directory can read all stored memories
- **Exercise caution**: While the MCP server warns the client LLM to avoid storing sensitive information, you should not rely solely on this safeguard
- **Backup considerations**: Be mindful when backing up or syncing directories containing `.memorious` folders

## Contributing

Contributions are welcome. Open a PR with tests.

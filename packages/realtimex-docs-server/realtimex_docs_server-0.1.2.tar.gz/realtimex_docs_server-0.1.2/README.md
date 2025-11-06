# realtimex-docs-server

A FastMCP-based MCP server that makes local documentation available to RealTimeX agents.

## Features
- Serve documentation from a configurable directory via CLI flag or environment variable
- List every documentation file in a single call
- Read documents as UTF-8 text with optional `offset`/`limit` line slicing
- Transport over stdio for MCP clients

## Configuration
Set the documentation root via the `--docs-path` CLI option or the `REALTIMEX_DOCS_ROOT` environment variable (CLI flag takes precedence).

## Usage
```bash
uvx realtimex-docs-server --docs-path /path/to/docs
```

Once connected, agents can call the `list_documents` and `read_document` tools to explore the configured directory. `list_documents` returns the full file inventory, while `read_document` accepts `offset` and `limit` parameters to fetch a window of lines and returns plain UTF-8 content without added numbering.

## Development
```bash
# Install dependencies
uv sync

# Run style or test tooling as needed
uv run ruff check
uv run pytest
```

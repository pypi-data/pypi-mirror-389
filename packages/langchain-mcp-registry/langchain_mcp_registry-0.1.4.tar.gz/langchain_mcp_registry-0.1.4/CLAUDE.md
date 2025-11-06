# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`langchain-mcp-registry` is a Python library that bridges the MCP (Model Context Protocol) Registry with LangChain. It enables automatic discovery of MCP servers from the registry and seamless conversion to LangChain-compatible tools.

**Core functionality:**
- Fetch server metadata from registry.modelcontextprotocol.io
- Convert registry server configurations to MCP-compatible formats
- Load MCP servers as LangChain tools for agent workflows
- CLI for searching, inspecting, and testing registry servers

## Development Commands

### Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=langchain_mcp_registry --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run single test function
pytest tests/test_client.py::test_search_servers -v

# Run tests with specific markers
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m agent        # Agent tests (requires API keys)
pytest -m "not slow"   # Skip slow tests

# Run tests with verbose output
pytest -v
```

### Code Quality
```bash
# Format code (automatically fixes issues)
black src/ tests/

# Lint code (reports issues)
ruff check src/ tests/

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### CLI Usage
```bash
# Search for servers
mcp-registry search weather
mcp-registry search github --limit 5

# Get server details
mcp-registry info @modelcontextprotocol/server-brave-search
mcp-registry info server-github --version 1.0.0

# Generate MCP configuration
mcp-registry config server-brave-search
mcp-registry config server-github --output config.json

# List available versions
mcp-registry versions server-brave-search

# Test loading server tools
mcp-registry test server-brave-search "search query"
```

## Architecture

### Three-Layer Design

The library follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         Application Layer               │
│  - CLI (cli.py)                        │
│  - MCPToolLoader (loader.py)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Conversion Layer                │
│  - RegistryToMCPConverter (converter.py)│
│  - Handles stdio/HTTP/SSE transports   │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│         Data Layer                      │
│  - MCPRegistryClient (client.py)       │
│  - Pydantic Models (models.py)         │
└─────────────────────────────────────────┘
```

**Layer responsibilities:**
- **Data Layer**: HTTP communication with registry API, JSON parsing, caching
- **Conversion Layer**: Transform registry formats → MCP formats, handle transport differences
- **Application Layer**: High-level interfaces for tool loading and CLI commands

### Key Components

**MCPRegistryClient** (client.py):
- Async HTTP client for registry.modelcontextprotocol.io
- Methods: `search_servers()`, `get_server_details()`, `get_server_versions()`
- Handles caching, pagination, error responses

**RegistryToMCPConverter** (converter.py):
- Converts registry server configs → MCP configs (compatible with langchain-mcp-adapters)
- Priority: remotes (HTTP/SSE) > packages (stdio)
- Handles: command/args building, env variables, headers, transport types
- Critical methods: `convert()`, `_convert_from_remote()`, `_convert_from_package()`

**MCPToolLoader** (loader.py):
- Uses MultiServerMCPClient from langchain-mcp-adapters
- Wraps conversion + loading into single API
- Methods: `load_from_registry()`, `load_multiple()`, `search_and_load()`
- Supports env/header/args overrides per server

**Models** (models.py):
- Pydantic models for all registry data structures
- Key models: `MCPServer`, `ServerPackage`, `MCPConfig`, `Remote`, `Transport`
- Handles field aliases (camelCase → snake_case)

### Transport Types

The converter handles three transport types:

1. **stdio**: Local process communication
   - Requires: command, args
   - Optional: env, cwd
   - Example: `npx -y @package/server@1.0.0`

2. **sse** (Server-Sent Events): HTTP streaming
   - Requires: url
   - Optional: headers, timeout
   - Used for remote streaming servers

3. **streamable_http**: HTTP with streaming
   - Same as SSE but different protocol variant
   - Requires: url
   - Optional: headers, timeout

**Conversion priority**: If server has `remotes` field, use HTTP/SSE. Otherwise, use stdio from `packages`.

## Important Patterns

### Async Context Managers

All main classes use async context managers to ensure proper cleanup:

```python
async with MCPRegistryClient() as client:
    servers = await client.search_servers("weather")

async with MCPToolLoader() as loader:
    tools = await loader.load_from_registry("server-name")
```

**Why**: Ensures HTTP connections close, resources cleanup properly.

### Environment Variable Handling

The converter processes env vars with special rules:
- Required secrets without values → placeholder: `<REQUIRED: description>`
- Non-secret env vars → added to config
- Supports both stdio (env dict) and HTTP (headers) transports
- Header variable substitution: `{var_name}` → resolved from env

### Configuration Overrides

MCPToolLoader supports runtime overrides for flexibility:

```python
# Override environment variables (stdio)
tools = await loader.load_from_registry(
    "server-name",
    env_overrides={"API_KEY": "my-key"}
)

# Override headers (HTTP/SSE)
tools = await loader.load_from_registry(
    "remote-server",
    header_overrides={"Authorization": "Bearer token"}
)

# Override arguments (stdio)
tools = await loader.load_from_registry(
    "server-name",
    args_overrides=["--verbose", "--debug"]
)
```

**Use case**: When server requires secrets/tokens not in registry config.

### Error Handling

Custom exception hierarchy (exceptions.py):
- `MCPRegistryError` (base)
  - `ServerNotFoundError`: Server doesn't exist in registry
  - `RegistryConnectionError`: Network/API failures
  - `ConfigConversionError`: Invalid/unsupported server config
  - `ToolLoadError`: Failed to load tools from server
  - `InvalidConfigError`: Invalid configuration parameters

**Pattern**: Catch specific exceptions for different error scenarios.

## Testing Strategy

### Test Organization

Tests use pytest markers for categorization:
- `@pytest.mark.unit`: Fast, isolated tests with mocks
- `@pytest.mark.integration`: Real registry API calls
- `@pytest.mark.agent`: End-to-end agent tests (requires API keys)
- `@pytest.mark.slow`: Long-running tests

### Key Fixtures (conftest.py)

- `registry_client`: Async MCPRegistryClient instance
- `converter`: RegistryToMCPConverter instance
- `tool_loader`: Async MCPToolLoader instance
- `sample_servers`: Pre-fetched weather servers
- `llm_config`: LLM config (supports OpenAI or DeepSeek)

### Environment Variables for Tests

Create `.env` file for agent tests:
```bash
OPENAI_API_KEY=sk-...
# OR
DEEPSEEK_API_KEY=sk-...
```

**Note**: Integration tests require internet. Agent tests require API keys.

## Code Style Requirements

**Type Hints**: Required on all function signatures
```python
async def search_servers(
    self,
    query: str | None = None,
    limit: int = 30,
) -> list[MCPServer]:
```

**Docstrings**: Required for public APIs
- Class docstrings: Purpose, usage example
- Method docstrings: Args, Returns, Raises, Example

**Line Length**: 100 characters (enforced by black)

**Import Order**: Enforced by ruff (stdlib → third-party → local)

## Common Development Tasks

### Adding a New Registry API Endpoint

1. Add method to `MCPRegistryClient` (client.py)
2. Add/update Pydantic models if response structure changes (models.py)
3. Write unit tests with mocks (tests/test_client.py)
4. Write integration test with real API (tests/test_integration.py)

### Adding a New Transport Type

1. Add transport handling in `RegistryToMCPConverter._convert_from_package()` (converter.py)
2. Add validation in `validate_config()` (converter.py)
3. Update `MCPConfig` model if new fields needed (models.py)
4. Add tests in tests/test_converter.py

### Adding a New CLI Command

1. Add command function using `@app.command()` decorator (cli.py)
2. Create async implementation function (prefix with `_`)
3. Use `typer.Argument()` and `typer.Option()` for parameters
4. Use `rich` for formatted output (Table, Panel, Syntax)
5. Handle errors with console.print + typer.Exit(1)
6. Test manually with different inputs

## Dependencies

**Core dependencies:**
- `httpx`: Async HTTP client for registry API
- `pydantic`: Data validation and models
- `langchain-mcp-adapters`: MCP server integration
- `typer[all]`: CLI framework
- `rich`: Terminal formatting
- `aiofiles`: Async file I/O for caching
- `platformdirs`: Cross-platform cache directories

**Dev dependencies:**
- `pytest` + `pytest-asyncio` + `pytest-cov`: Testing
- `black`: Code formatting
- `ruff`: Linting
- `mypy`: Type checking
- `pre-commit`: Git hooks

## Python Version

**Minimum**: Python 3.11+

**Reason**: Uses new union type syntax (`str | None`) and other 3.11+ features.

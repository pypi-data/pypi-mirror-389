# Examples for langchain-mcp-registry

This directory contains usage examples for the langchain-mcp-registry package.

## Quick Start

### 0. Setup Environment Variables (Optional)

For examples that use LLM API (DeepSeek recommended):

```bash
# Copy the example env file
cp .env.example .env

# Edit .env and add your API keys
# DEEPSEEK_API_KEY=sk-your-key-here
```

Or export directly:
```bash
export DEEPSEEK_API_KEY="sk-your-key-here"
```

**Note**: Example 4 uses DeepSeek by default. You can also use OpenAI or other compatible APIs.

### 1. Basic Usage (No Server Loading)

Run examples that don't require loading actual MCP servers:

```bash
python examples/basic_usage.py
```

This will run:
- **Example 1**: Search for servers in the registry
- **Example 2**: Get detailed server information

### 2. Test Tool Loading

Test loading tools from a real MCP server:

```bash
python examples/test_load_tools.py
```

This will:
- Load tools from `com.pulsemcp.servers/pulse-fetch`
- Demonstrate the complete search and load workflow

**Note**: This requires npx and will download the MCP server package.

## Available Examples

### basic_usage.py

Complete usage examples covering all features:

1. **example_1_search_servers()** - Search the MCP registry
2. **example_2_get_server_details()** - Get detailed server information
3. **example_3_load_tools()** - Load tools from a server (commented out)
4. **example_4_use_with_langchain()** - Use tools with LangChain agent and DeepSeek (requires DEEPSEEK_API_KEY)
   - Demonstrates Python package loading with correct `python -m module_name` format
   - Uses only 2 tools to avoid DeepSeek context length limits
   - Shows complete workflow: load tools → create agent → execute query
5. **example_5_load_multiple_servers_concurrent()** - NEW! Concurrent loading (commented out)
6. **example_5b_load_multiple_servers_sequential()** - Sequential loading for comparison (commented out)
7. **example_6_search_and_load()** - Search and load workflow (commented out)

### test_load_tools.py

Simple tool loading tests:

- **test_load_single_server()** - Load from single server
- **test_concurrent_loading()** - Search and load workflow

### test_all_package_types.py

Comprehensive test for all package types:

- **NPM Package** - Tests `npx -y @package/name@version` format and tool loading
- **PyPI Package** - Tests `python -m module_name` format and tool loading
- **Docker Package** - Tests `docker image:version` format (config generation only)

This test verifies the converter correctly handles all three registry types and generates proper command-line arguments for each.

## Requirements

### Basic Examples (1-2)
- No additional dependencies
- Internet connection to access registry

### Tool Loading Examples (3-7)
- **Node.js/npx** for npm-based servers
- **Python packages** for pypi-based servers
- **Docker** for docker-based servers

### LangChain Agent Example (4)
- DeepSeek API key (recommended): `export DEEPSEEK_API_KEY="sk-..."`
  - Cost-effective and powerful
  - Note: Example uses only 2 tools to stay within context limits
- Or OpenAI API key: `export OPENAI_API_KEY="sk-..."`

## Migration from langchain-mcp-tools

This package now uses the official **langchain-mcp-adapters** instead of the third-party langchain-mcp-tools.

**Benefits:**
- ✅ Concurrent loading works perfectly (no bugs!)
- ✅ Official support from LangChain AI
- ✅ Better API design with session management
- ✅ All existing code works without changes

**Example of concurrent loading:**

```python
async with MCPToolLoader() as loader:
    # Load multiple servers in PARALLEL!
    tools, cleanup = await loader.load_multiple([
        "server1",
        "server2",
        "server3"
    ])

    # All tools loaded concurrently
    print(f"Loaded {len(tools)} tools!")

    await cleanup()
```

## Common Issues

### 1. Module not found errors

Install the package in development mode:

```bash
pip install -e .
```

### 2. Server loading fails

Some servers in the registry may:
- Lack proper package configuration
- Require specific runtime environments
- Need API keys or credentials

Try using well-known servers like:
- `com.pulsemcp.servers/pulse-fetch`
- `io.github.brave/brave-search-mcp-server`

### 3. Python/npm warnings

These are harmless and from the MCP servers themselves:

```
npm warn cli npm v11.6.0 does not support Node.js v21.7.2
```

You can safely ignore these warnings.

## Further Documentation

See the main README.md for complete documentation and API reference.

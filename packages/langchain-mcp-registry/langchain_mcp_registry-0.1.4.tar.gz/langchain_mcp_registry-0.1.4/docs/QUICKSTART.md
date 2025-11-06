# Quick Start Guide

Get started with langchain-mcp-registry in 5 minutes.

## Installation

```bash
pip install langchain-mcp-registry
```

## Basic Usage

### 1. Search for MCP Servers

```python
import asyncio
from langchain_mcp_registry import MCPRegistryClient

async def search_example():
    async with MCPRegistryClient() as client:
        # Search for servers
        servers = await client.search_servers(query="weather", limit=5)

        for server in servers:
            print(f"- {server.name}: {server.description}")

asyncio.run(search_example())
```

### 2. Load Tools from Registry

```python
from langchain_mcp_registry import MCPToolLoader

async def load_tools_example():
    async with MCPToolLoader() as loader:
        # Load tools from a specific server
        tools, cleanup = await loader.load_from_registry(
            "@modelcontextprotocol/server-brave-search",
            version="latest"
        )

        print(f"Loaded {len(tools)} tools")

        # Don't forget to cleanup
        await cleanup()

asyncio.run(load_tools_example())
```

### 3. Use with LangChain Agent

```python
from langchain_mcp_registry import MCPToolLoader
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

async def agent_example():
    async with MCPToolLoader() as loader:
        # Load tools
        tools, cleanup = await loader.load_from_registry(
            "@modelcontextprotocol/server-brave-search"
        )

        # Create agent
        llm = ChatOpenAI(model="gpt-4")
        agent = create_react_agent(llm, tools)

        # Use agent
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": "What's the weather in SF?"}]
        })

        print(result["messages"][-1].content)

        await cleanup()

asyncio.run(agent_example())
```

## CLI Usage

### Search Servers

```bash
# Search for servers
mcp-registry search weather

# Limit results
mcp-registry search github --limit 5

# Show detailed information
mcp-registry search --details
```

### Get Server Info

```bash
# Get information about a specific server
mcp-registry info @modelcontextprotocol/server-brave-search

# Get specific version
mcp-registry info server-github --version 1.0.0
```

### Generate Configuration

```bash
# Generate MCP configuration
mcp-registry config server-brave-search

# Save to file
mcp-registry config server-github --output config.json
```

### List Versions

```bash
# List all available versions
mcp-registry versions server-brave-search
```

## Environment Variables

Some MCP servers require environment variables:

```python
async def env_example():
    async with MCPToolLoader() as loader:
        tools, cleanup = await loader.load_from_registry(
            "@modelcontextprotocol/server-brave-search",
            env_overrides={"BRAVE_API_KEY": "your-api-key"}
        )
        # Use tools...
        await cleanup()
```

## Common Patterns

### Load Multiple Servers

```python
async def multiple_servers():
    async with MCPToolLoader() as loader:
        tools, cleanup = await loader.load_multiple([
            "@modelcontextprotocol/server-brave-search",
            "@modelcontextprotocol/server-github",
            "@modelcontextprotocol/server-filesystem",
        ])
        # Use combined tools...
        await cleanup()
```

### Search and Auto-Load

```python
async def search_and_load():
    async with MCPToolLoader() as loader:
        # Search for "database" and load top 3 servers
        tools, cleanup = await loader.search_and_load(
            query="database",
            max_servers=3
        )
        # Use tools...
        await cleanup()
```

## Next Steps

- Check out [examples/](../examples/) for more detailed examples
- Read the [API Reference](API.md) for complete documentation
- See [CONTRIBUTING.md](../CONTRIBUTING.md) to contribute

## Troubleshooting

### Server Not Found

```python
from langchain_mcp_registry.exceptions import ServerNotFoundError

try:
    tools, cleanup = await loader.load_from_registry("nonexistent-server")
except ServerNotFoundError as e:
    print(f"Server not found: {e}")
```

### Connection Errors

```python
from langchain_mcp_registry.exceptions import RegistryConnectionError

try:
    servers = await client.search_servers()
except RegistryConnectionError as e:
    print(f"Connection failed: {e}")
```

### Tool Loading Errors

```python
from langchain_mcp_registry.exceptions import ToolLoadError

try:
    tools, cleanup = await loader.load_from_registry("server-name")
except ToolLoadError as e:
    print(f"Failed to load tools: {e}")
```

## Support

- GitHub Issues: https://github.com/foresee-ai/langchain-mcp-registry/issues
- Discussions: https://github.com/foresee-ai/langchain-mcp-registry/discussions
- Email: dev@foresee.ai

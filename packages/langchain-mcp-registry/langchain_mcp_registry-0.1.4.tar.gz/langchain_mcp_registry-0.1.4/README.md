# 🔗 LangChain MCP Registry

> Seamlessly integrate MCP Registry servers into your LangChain workflows

[![PyPI version](https://badge.fury.io/py/langchain-mcp-registry.svg)](https://badge.fury.io/py/langchain-mcp-registry)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 🌟 Features

- 🔍 **Automatic Discovery**: Search and discover MCP servers from the official registry
- 🔄 **Seamless Integration**: Convert registry servers to LangChain-compatible tools
- 🚀 **Zero Configuration**: Works out of the box with sensible defaults
- 🛡️ **Type Safe**: Full type hints and Pydantic models
- 🎯 **CLI & Python API**: Use via command line or programmatically
- 📦 **Multiple Transports**: Support for stdio, HTTP, SSE

## 🚀 Quick Start

### Installation

```bash
pip install langchain-mcp-registry
```

### Python API

```python
from langchain_mcp_registry import MCPRegistryClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

# 1. Discover servers from registry
async with MCPRegistryClient() as client:
    servers = await client.search_servers(query="weather")

    # 2. Auto-convert to LangChain tools
    tools = await client.load_tools(servers[0])

    # 3. Use in LangChain agent
    llm = ChatOpenAI(model="gpt-4")
    agent = create_react_agent(llm, tools)

    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "What's the weather in SF?"}]
    })
```

### CLI Usage

```bash
# Search for servers
mcp-registry search weather

# List server details
mcp-registry info @modelcontextprotocol/server-brave-search

# Install and test a server
mcp-registry install @modelcontextprotocol/server-brave-search
mcp-registry test brave-search "search for AI news"
```

## 📚 Documentation

### Registry Client

```python
from langchain_mcp_registry import MCPRegistryClient

client = MCPRegistryClient(
    registry_url="https://registry.modelcontextprotocol.io",
    timeout=30.0,
    cache_ttl=3600
)

# Search with filters
servers = await client.search_servers(
    query="github",
    limit=10,
    version="latest"
)

# Get server details
server_details = await client.get_server_details(
    name="@modelcontextprotocol/server-github",
    version="latest"
)
```

### Configuration Converter

```python
from langchain_mcp_registry import RegistryToMCPConverter

converter = RegistryToMCPConverter()

# Convert registry server to MCP config
mcp_config = converter.convert(registry_server)
# Output: {"command": "npx", "args": [...], "env": {...}}

# Validate configuration
is_valid = converter.validate_config(mcp_config)
```

### Tool Loader

```python
from langchain_mcp_registry import MCPToolLoader

loader = MCPToolLoader()

# Load tools from registry server
tools = await loader.load_from_registry(
    server_name="@modelcontextprotocol/server-everything",
    version="latest"
)

# Load multiple servers
all_tools = await loader.load_multiple([
    "server-brave-search",
    "server-github",
    "server-filesystem"
])
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    LangChain Agent                      │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              LangChain MCP Registry                     │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────┐    │
│  │   Registry   │  │ Converter  │  │    Tool     │    │
│  │   Client     │─▶│  (R → M)   │─▶│   Loader    │    │
│  └──────────────┘  └────────────┘  └─────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│          MCP Registry (modelcontextprotocol.io)         │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Advanced Usage

### Custom Registry

```python
client = MCPRegistryClient(
    registry_url="https://your-private-registry.com",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### Error Handling

```python
from langchain_mcp_registry.exceptions import (
    ServerNotFoundError,
    InvalidConfigError,
    RegistryConnectionError
)

try:
    tools = await client.load_tools("non-existent-server")
except ServerNotFoundError:
    print("Server not found in registry")
except InvalidConfigError as e:
    print(f"Invalid configuration: {e}")
```

### Caching

```python
# Enable local caching for faster repeated access
client = MCPRegistryClient(
    cache_enabled=True,
    cache_ttl=7200,  # 2 hours
    cache_dir="~/.mcp-registry-cache"
)
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [LangChain](https://www.langchain.com/)
- [Anthropic](https://www.anthropic.com/)

## 🔗 Links

- **PyPI**: https://pypi.org/project/langchain-mcp-registry/
- **GitHub**: https://github.com/ChangjunZhao/langchain-mcp-registry
- **Issues**: https://github.com/ChangjunZhao/langchain-mcp-registry/issues

---

Made with ❤️ for the LangChain and MCP communities

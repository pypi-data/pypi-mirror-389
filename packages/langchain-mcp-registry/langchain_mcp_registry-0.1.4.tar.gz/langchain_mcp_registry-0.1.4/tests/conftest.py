"""
Pytest configuration and fixtures
"""

import os
from pathlib import Path

import pytest

from langchain_mcp_registry import (
    MCPRegistryClient,
    MCPToolLoader,
    RegistryToMCPConverter,
)

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass  # python-dotenv not installed, skip


@pytest.fixture
async def registry_client():
    """Fixture for MCPRegistryClient"""
    async with MCPRegistryClient() as client:
        yield client


@pytest.fixture
def converter():
    """Fixture for RegistryToMCPConverter"""
    return RegistryToMCPConverter()


@pytest.fixture
async def tool_loader():
    """Fixture for MCPToolLoader"""
    async with MCPToolLoader() as loader:
        yield loader


@pytest.fixture
async def sample_servers(registry_client):
    """Fixture to get sample servers for testing"""
    servers = await registry_client.search_servers(query="weather", limit=5)
    return servers


@pytest.fixture
async def server_with_packages(registry_client):
    """Fixture to get a server with package configuration"""
    servers = await registry_client.search_servers(query="fetch", limit=20)
    for server in servers:
        if server.packages and len(server.packages) > 0:
            return server
    return None


@pytest.fixture
def sample_server_dict():
    """Fixture with sample server data"""
    return {
        "name": "test-server",
        "title": "Test Server",
        "description": "A test MCP server",
        "version": "1.0.0",
        "packages": [
            {
                "registryType": "npm",
                "identifier": "@test/mcp-server",
                "version": "1.0.0",
                "transport": {"type": "stdio"},
            }
        ],
    }


@pytest.fixture
def llm_config():
    """Fixture for LLM configuration (OpenAI or DeepSeek)"""
    openai_key = os.environ.get("OPENAI_API_KEY")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")

    if deepseek_key:
        return {
            "provider": "deepseek",
            "api_key": deepseek_key,
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
        }
    elif openai_key:
        return {
            "provider": "openai",
            "api_key": openai_key,
            "model": "gpt-4o-mini",
            "base_url": None,
        }
    else:
        return None


@pytest.fixture
def openai_api_key():
    """Fixture for OpenAI API key (deprecated, use llm_config instead)"""
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")

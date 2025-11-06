"""
Unit tests for MCPRegistryClient
"""

import pytest
from langchain_mcp_registry import MCPRegistryClient
from langchain_mcp_registry.exceptions import ServerNotFoundError, RegistryConnectionError


@pytest.mark.unit
class TestMCPRegistryClient:
    """Test MCPRegistryClient functionality"""

    async def test_client_initialization(self):
        """Test client can be initialized"""
        client = MCPRegistryClient()
        assert client is not None
        assert client.registry_url == MCPRegistryClient.DEFAULT_REGISTRY_URL
        await client.close()

    async def test_client_context_manager(self):
        """Test async context manager"""
        async with MCPRegistryClient() as client:
            assert client is not None
            servers = await client.search_servers(limit=1)
            assert isinstance(servers, list)

    async def test_search_servers_basic(self, registry_client):
        """Test basic server search"""
        servers = await registry_client.search_servers(limit=5)
        assert len(servers) > 0
        assert len(servers) <= 5

        # Validate first server structure
        server = servers[0]
        assert server.name is not None
        assert server.version is not None

    async def test_search_servers_with_query(self, registry_client):
        """Test search with query string"""
        servers = await registry_client.search_servers(query="weather", limit=10)
        assert len(servers) > 0

        # Check that results contain weather-related servers
        names = " ".join([s.name.lower() for s in servers])
        assert "weather" in names or any(
            "weather" in s.description.lower() for s in servers if s.description
        )

    async def test_get_server_details(self, registry_client, server_with_packages):
        """Test getting server details"""
        if not server_with_packages:
            pytest.skip("No suitable server found")

        server = server_with_packages
        details = await registry_client.get_server_details(server.name, server.version)

        assert details.name == server.name
        assert details.version == server.version
        assert details.description is not None

    async def test_get_server_details_not_found(self, registry_client):
        """Test getting details for non-existent server"""
        with pytest.raises(ServerNotFoundError):
            await registry_client.get_server_details("non-existent-server-12345", "1.0.0")

    async def test_url_encoding(self, registry_client):
        """Test URL encoding for server names with special characters"""
        # Search for a server with / in name
        servers = await registry_client.search_servers(limit=50)

        servers_with_slash = [s for s in servers if "/" in s.name]
        if servers_with_slash:
            server = servers_with_slash[0]
            # This should not raise an error
            details = await registry_client.get_server_details(server.name, server.version)
            assert details.name == server.name

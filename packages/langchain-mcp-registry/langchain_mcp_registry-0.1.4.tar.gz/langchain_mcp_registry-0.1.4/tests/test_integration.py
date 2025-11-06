"""
Integration tests for langchain-mcp-registry
"""

import pytest
from langchain_mcp_registry import MCPRegistryClient, RegistryToMCPConverter, MCPToolLoader


@pytest.mark.integration
class TestIntegration:
    """Integration tests combining multiple components"""

    async def test_full_search_and_convert_workflow(self):
        """Test complete workflow: search -> get details -> convert"""
        async with MCPRegistryClient() as client:
            # Step 1: Search
            servers = await client.search_servers(query="fetch", limit=20)
            assert len(servers) > 0

            # Find a server with packages
            target_server = None
            for server in servers:
                if server.packages and len(server.packages) > 0:
                    target_server = server
                    break

            if not target_server:
                pytest.skip("No server with packages found")

            # Step 2: Get details
            details = await client.get_server_details(target_server.name, target_server.version)
            assert details.name == target_server.name

            # Step 3: Convert
            converter = RegistryToMCPConverter()
            config = converter.convert(details)

            assert config.command is not None
            assert len(config.args) > 0
            assert config.transport in ["stdio", "http", "sse"]

    async def test_version_handling_workflow(self):
        """Test handling different versions"""
        async with MCPRegistryClient() as client:
            # Get any server
            servers = await client.search_servers(limit=10)
            if not servers:
                pytest.skip("No servers found")

            server = servers[0]

            # Get latest version
            latest = await client.get_server_details(server.name, "latest")
            assert latest is not None

            # Version should be set
            assert latest.version is not None

    async def test_concurrent_operations(self):
        """Test running multiple operations concurrently"""
        import asyncio

        async def search_task(query):
            async with MCPRegistryClient() as client:
                return await client.search_servers(query=query, limit=5)

        # Run multiple searches concurrently
        tasks = [
            search_task("weather"),
            search_task("github"),
            search_task("fetch"),
        ]

        results = await asyncio.gather(*tasks)

        # All should return results
        assert all(len(r) > 0 for r in results)

    async def test_resource_cleanup_workflow(self):
        """Test that resources are properly cleaned up"""
        client = MCPRegistryClient()

        async with client:
            servers = await client.search_servers(limit=1)
            assert len(servers) > 0

        # Client should be closed after context
        assert client.client.is_closed

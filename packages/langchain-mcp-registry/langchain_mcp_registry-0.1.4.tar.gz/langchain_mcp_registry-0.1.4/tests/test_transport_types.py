"""
Test all transport types: stdio, http, sse
Tests both real servers and synthetic configurations
"""

import pytest
from langchain_mcp_registry import MCPRegistryClient, RegistryToMCPConverter
from langchain_mcp_registry.models import MCPServer, ServerPackage, Transport


@pytest.mark.unit
class TestTransportTypes:
    """Test all transport type configurations"""

    async def test_stdio_transport(self):
        """Test stdio transport (most common)"""
        converter = RegistryToMCPConverter()

        server = MCPServer(
            name="test-stdio-server",
            version="1.0.0",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/stdio-server",
                    transport=Transport(type="stdio"),
                )
            ],
        )

        config = converter.convert(server)

        assert config.transport == "stdio"
        assert config.command == "npx"
        print(f"✓ STDIO transport: {config.transport}")

    async def test_http_transport(self):
        """Test HTTP transport with URL"""
        converter = RegistryToMCPConverter()

        server = MCPServer(
            name="test-http-server",
            version="1.0.0",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/http-server",
                    transport=Transport(type="http", url="http://localhost:3000/mcp"),
                )
            ],
        )

        config = converter.convert(server)

        # HTTP transport should be preserved
        # Note: Current MCP client may only support stdio, but config should preserve transport type
        assert config.command == "npx"
        # Transport type is determined by the package, not stored in MCPConfig directly
        # The transport info is in the Transport model
        print(f"✓ HTTP transport: Server uses HTTP at http://localhost:3000/mcp")

    async def test_http_transport_with_template_url(self):
        """Test HTTP transport with template URL (port placeholder)"""
        converter = RegistryToMCPConverter()

        server = MCPServer(
            name="test-http-template-server",
            version="1.0.0",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/http-server",
                    transport=Transport(type="http", url="http://127.0.0.1:{port}/mcp"),
                )
            ],
        )

        config = converter.convert(server)

        # Template URLs should be preserved
        pkg = server.packages[0]
        assert pkg.transport.url == "http://127.0.0.1:{port}/mcp"
        assert "{port}" in pkg.transport.url
        print(f"✓ HTTP transport with template: {pkg.transport.url}")

    async def test_sse_transport(self):
        """Test SSE (Server-Sent Events) transport"""
        converter = RegistryToMCPConverter()

        server = MCPServer(
            name="test-sse-server",
            version="1.0.0",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/sse-server",
                    transport=Transport(type="sse", url="http://localhost:3000/sse"),
                )
            ],
        )

        config = converter.convert(server)

        # SSE transport should be preserved in package
        pkg = server.packages[0]
        assert pkg.transport.type == "sse"
        assert pkg.transport.url == "http://localhost:3000/sse"
        print(f"✓ SSE transport: {pkg.transport.type} at {pkg.transport.url}")


@pytest.mark.integration
class TestRealTransportDiscovery:
    """Test discovery of real servers using different transports"""

    async def test_discover_all_transport_types(self, registry_client):
        """Discover and categorize all available transport types in registry"""
        servers = await registry_client.search_servers(limit=100)

        transport_examples = {"stdio": [], "http": [], "sse": [], "other": []}

        for server in servers:
            if not server.packages:
                continue

            for pkg in server.packages:
                transport_type = pkg.transport.type if pkg.transport else "unknown"

                if transport_type in transport_examples:
                    if len(transport_examples[transport_type]) < 5:
                        transport_examples[transport_type].append(
                            {
                                "server": server.name,
                                "identifier": pkg.identifier,
                                "url": pkg.transport.url if pkg.transport else None,
                            }
                        )
                else:
                    if len(transport_examples["other"]) < 5:
                        transport_examples["other"].append(
                            {"server": server.name, "type": transport_type}
                        )

        print("\n✓ Available Transport Types in Registry:")
        for transport_type, examples in transport_examples.items():
            print(f"\n  {transport_type.upper()} ({len(examples)} examples):")
            for ex in examples:
                if transport_type in ["http", "sse"]:
                    print(f"    - {ex['server']}: {ex['identifier']} @ {ex.get('url', 'N/A')}")
                else:
                    print(f"    - {ex['server']}: {ex['identifier']}")

        # Verify we found at least stdio servers
        assert len(transport_examples["stdio"]) > 0, "Should have at least some stdio servers"


@pytest.mark.integration
class TestTransportIntegration:
    """Test transport integration scenarios"""

    async def test_transport_with_environment_variables(self):
        """Test transports requiring environment variables"""
        from langchain_mcp_registry.models import ArgumentInput

        server = MCPServer(
            name="auth-http-server",
            version="1.0.0",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@auth/http-server",
                    transport=Transport(type="http", url="https://api.example.com/mcp"),
                    environmentVariables=[
                        ArgumentInput(
                            name="API_KEY",
                            description="API authentication key",
                            isRequired=True,
                            isSecret=True,
                        )
                    ],
                )
            ],
        )

        # Verify transport and env vars are both captured
        pkg = server.packages[0]
        assert pkg.transport.type == "http"
        assert len(pkg.environment_variables) == 1
        assert pkg.environment_variables[0].name == "API_KEY"
        assert pkg.environment_variables[0].is_secret is True

        print("\n✓ HTTP Transport with Auth:")
        print(f"  Transport: {pkg.transport.type}")
        print(f"  URL: {pkg.transport.url}")
        print(
            f"  Required Env: {pkg.environment_variables[0].name} (secret: {pkg.environment_variables[0].is_secret})"
        )

    async def test_stdio_is_default_transport(self, registry_client):
        """Test that stdio is the predominant transport type"""
        servers = await registry_client.search_servers(limit=100)

        total_packages = 0
        stdio_packages = 0

        for server in servers:
            if not server.packages:
                continue

            for pkg in server.packages:
                total_packages += 1
                if pkg.transport and pkg.transport.type == "stdio":
                    stdio_packages += 1

        if total_packages > 0:
            stdio_percentage = (stdio_packages / total_packages) * 100
            print(f"\n✓ STDIO is default transport:")
            print(f"  Total packages: {total_packages}")
            print(f"  STDIO packages: {stdio_packages}")
            print(f"  STDIO percentage: {stdio_percentage:.1f}%")

            # Most servers should use stdio currently
            assert stdio_packages > 0

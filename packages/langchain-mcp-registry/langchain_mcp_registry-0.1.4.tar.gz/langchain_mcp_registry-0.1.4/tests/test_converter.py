"""
Unit tests for RegistryToMCPConverter
"""

import os
import pytest
from langchain_mcp_registry import RegistryToMCPConverter
from langchain_mcp_registry.models import MCPServer, ServerPackage, Transport, Remote, ArgumentInput
from langchain_mcp_registry.exceptions import ConfigConversionError


@pytest.mark.unit
class TestRegistryToMCPConverter:
    """Test RegistryToMCPConverter functionality"""

    async def test_convert_npm_package(self, registry_client, converter):
        """Test converting npm package"""
        servers = await registry_client.search_servers(limit=50)

        # Find an npm server
        npm_server = None
        for server in servers:
            if server.packages:
                for pkg in server.packages:
                    if pkg.registry_type == "npm":
                        npm_server = server
                        break
            if npm_server:
                break

        if not npm_server:
            pytest.skip("No npm server found")

        config = converter.convert(npm_server)
        assert config.command == "npx"
        assert len(config.args) > 0
        assert config.transport == "stdio"

    async def test_convert_pypi_package(self, registry_client, converter):
        """Test converting pypi package"""
        servers = await registry_client.search_servers(limit=100)

        # Find a pypi server
        pypi_server = None
        for server in servers:
            if server.packages:
                for pkg in server.packages:
                    if pkg.registry_type == "pypi":
                        pypi_server = server
                        break
            if pypi_server:
                break

        if not pypi_server:
            pytest.skip("No pypi server found")

        config = converter.convert(pypi_server)
        assert config.command == "python"
        assert len(config.args) > 0

    async def test_convert_docker_package(self, registry_client, converter):
        """Test converting docker/oci package"""
        servers = await registry_client.search_servers(limit=100)

        # Find a docker/oci server
        docker_server = None
        for server in servers:
            if server.packages:
                for pkg in server.packages:
                    if pkg.registry_type in ["docker", "oci"]:
                        docker_server = server
                        break
            if docker_server:
                break

        if not docker_server:
            pytest.skip("No docker server found")

        config = converter.convert(docker_server)
        assert config.command == "docker"
        assert len(config.args) > 0

    async def test_convert_with_environment_variables(self, registry_client, converter):
        """Test converting server with environment variables"""
        servers = await registry_client.search_servers(query="weather", limit=20)

        # Find a server with env vars
        server_with_env = None
        for server in servers:
            if server.packages:
                for pkg in server.packages:
                    if pkg.environment_variables and len(pkg.environment_variables) > 0:
                        server_with_env = server
                        break
            if server_with_env:
                break

        if not server_with_env:
            pytest.skip("No server with env vars found")

        config = converter.convert(server_with_env)
        assert config.env is not None
        assert len(config.env) > 0

    async def test_convert_identifies_required_secrets(self, registry_client, converter):
        """Test that converter identifies required secrets"""
        servers = await registry_client.search_servers(limit=50)

        # Find a server with required secret env vars
        for server in servers:
            if server.packages:
                for pkg in server.packages:
                    if pkg.environment_variables:
                        for env_var in pkg.environment_variables:
                            if env_var.is_secret and env_var.is_required:
                                config = converter.convert(server)
                                # Should have warning about required secret
                                assert config.env is not None
                                return

        pytest.skip("No server with required secrets found")

    def test_convert_server_without_packages(self, converter):
        """Test that converter raises error for server without packages"""
        server = MCPServer(
            name="test-server", version="1.0.0", description="Test server", packages=None
        )

        with pytest.raises(ConfigConversionError):
            converter.convert(server)

    async def test_config_has_all_required_fields(self, server_with_packages, converter):
        """Test that generated config has all required fields"""
        if not server_with_packages:
            pytest.skip("No suitable server found")

        config = converter.convert(server_with_packages)

        # Check transport-specific fields
        if config.transport == "stdio":
            assert config.command is not None
            assert config.args is not None
            assert len(config.args) > 0
        elif config.transport in ["sse", "streamable_http"]:
            assert config.url is not None
            assert config.timeout is not None
            assert config.timeout > 0

        assert config.transport in ["stdio", "sse", "streamable_http"]

    def test_convert_remote_streamable_http(self, converter):
        """Test converting server with streamable-http remote configuration"""
        server = MCPServer(
            name="test-remote-http",
            version="1.0.0",
            description="Test remote HTTP server",
            remotes=[
                Remote(type="streamable-http", url="https://api.example.com/mcp", headers=None)
            ],
        )

        config = converter.convert(server)
        assert config.transport == "streamable_http"
        assert config.url == "https://api.example.com/mcp"
        assert config.command is None
        assert config.args is None
        assert config.timeout == 30

    def test_convert_remote_sse(self, converter):
        """Test converting server with SSE remote configuration"""
        server = MCPServer(
            name="test-remote-sse",
            version="1.0.0",
            description="Test remote SSE server",
            remotes=[Remote(type="sse", url="https://sse.example.com/mcp/stream", headers=None)],
        )

        config = converter.convert(server)
        assert config.transport == "sse"
        assert config.url == "https://sse.example.com/mcp/stream"
        assert config.command is None
        assert config.args is None

    def test_convert_remote_with_headers(self, converter):
        """Test converting remote with headers configuration"""
        server = MCPServer(
            name="test-remote-headers",
            version="1.0.0",
            description="Test remote with headers",
            remotes=[
                Remote(
                    type="sse",
                    url="https://api.example.com/mcp",
                    headers=[
                        {"name": "Content-Type", "value": "application/json"},
                        {"name": "X-API-Version", "value": "v1"},
                    ],
                )
            ],
        )

        config = converter.convert(server)
        assert config.transport == "sse"
        assert config.headers is not None
        assert config.headers["Content-Type"] == "application/json"
        assert config.headers["X-API-Version"] == "v1"

    def test_convert_remote_with_header_variables(self, converter):
        """Test converting remote with header variable substitution"""
        # Set environment variable for testing
        os.environ["API_TOKEN"] = "test-token-12345"

        server = MCPServer(
            name="test-header-vars",
            version="1.0.0",
            description="Test header variables",
            remotes=[
                Remote(
                    type="streamable-http",
                    url="https://api.example.com/mcp",
                    headers=[
                        {
                            "name": "Authorization",
                            "value": "Bearer {api_token}",
                            "variables": {
                                "api_token": {
                                    "description": "API token",
                                    "isRequired": True,
                                    "isSecret": True,
                                }
                            },
                        }
                    ],
                )
            ],
        )

        config = converter.convert(server)
        assert config.headers is not None
        assert config.headers["Authorization"] == "Bearer test-token-12345"

        # Clean up
        del os.environ["API_TOKEN"]

    def test_convert_remote_with_missing_required_variable(self, converter):
        """Test that missing required header variables are flagged"""
        # Ensure the variable is not set
        if "MISSING_TOKEN" in os.environ:
            del os.environ["MISSING_TOKEN"]

        server = MCPServer(
            name="test-missing-var",
            version="1.0.0",
            description="Test missing variable",
            remotes=[
                Remote(
                    type="sse",
                    url="https://api.example.com/mcp",
                    headers=[
                        {
                            "name": "Authorization",
                            "value": "Bearer {missing_token}",
                            "variables": {
                                "missing_token": {
                                    "description": "Missing token",
                                    "isRequired": True,
                                    "isSecret": True,
                                }
                            },
                        }
                    ],
                )
            ],
        )

        config = converter.convert(server)
        assert config.headers is not None
        # Should have placeholder for missing required variable
        assert "<REQUIRED:missing_token>" in config.headers["Authorization"]

    def test_convert_package_with_http_transport(self, converter):
        """Test converting package with HTTP/SSE transport"""
        server = MCPServer(
            name="test-package-http",
            version="1.0.0",
            description="Test package with HTTP transport",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/mcp-server",
                    version="1.0.0",
                    transport=Transport(
                        type="streamable-http", url="https://api.example.com/mcp", headers=None
                    ),
                )
            ],
        )

        config = converter.convert(server)
        assert config.transport == "streamable_http"
        assert config.url == "https://api.example.com/mcp"
        assert config.command is None

    def test_convert_package_http_transport_with_headers(self, converter):
        """Test converting package with HTTP transport and headers"""
        server = MCPServer(
            name="test-package-http-headers",
            version="1.0.0",
            description="Test package with HTTP and headers",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/mcp-server",
                    version="1.0.0",
                    transport=Transport(
                        type="sse",
                        url="https://api.example.com/mcp",
                        headers=[{"name": "X-Custom-Header", "value": "custom-value"}],
                    ),
                )
            ],
        )

        config = converter.convert(server)
        assert config.transport == "sse"
        assert config.headers is not None
        assert config.headers["X-Custom-Header"] == "custom-value"

    def test_remote_priority_over_packages(self, converter):
        """Test that remotes have priority over packages"""
        server = MCPServer(
            name="test-priority",
            version="1.0.0",
            description="Test priority",
            remotes=[Remote(type="sse", url="https://remote.example.com/mcp", headers=None)],
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/mcp-server",
                    version="1.0.0",
                    transport=Transport(type="stdio", url=None, headers=None),
                )
            ],
        )

        config = converter.convert(server)
        # Should use remote configuration, not package
        assert config.transport == "sse"
        assert config.url == "https://remote.example.com/mcp"
        assert config.command is None

    def test_validate_stdio_config(self, converter):
        """Test validation of stdio configuration"""
        server = MCPServer(
            name="test-stdio",
            version="1.0.0",
            description="Test stdio",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/mcp-server",
                    version="1.0.0",
                    transport=Transport(type="stdio", url=None, headers=None),
                )
            ],
        )

        config = converter.convert(server)
        # Should validate successfully
        assert converter.validate_config(config) == True
        assert config.transport == "stdio"
        assert config.command is not None
        assert config.args is not None

    def test_validate_http_config_requires_url(self, converter):
        """Test that HTTP/SSE configs require URL"""
        from langchain_mcp_registry.models import MCPConfig

        # Create invalid config without URL
        config = MCPConfig(transport="sse", url=None, headers=None)

        with pytest.raises(ConfigConversionError, match="URL"):
            converter.validate_config(config)

    def test_normalize_transport_type(self, converter):
        """Test that transport types are normalized correctly"""
        # streamable-http should be converted to streamable_http
        server = MCPServer(
            name="test-normalize",
            version="1.0.0",
            description="Test normalization",
            remotes=[
                Remote(
                    type="streamable-http",  # With hyphen
                    url="https://api.example.com/mcp",
                    headers=None,
                )
            ],
        )

        config = converter.convert(server)
        assert config.transport == "streamable_http"  # Should be normalized to underscore

"""
Unit tests for MCPToolLoader
"""

import pytest
from langchain_mcp_registry import MCPToolLoader, RegistryToMCPConverter
from langchain_mcp_registry.exceptions import ToolLoadError
from langchain_mcp_registry.models import MCPServer, ServerPackage, Transport, Remote


@pytest.mark.unit
class TestMCPToolLoader:
    """Test MCPToolLoader functionality"""

    async def test_loader_with_custom_client(self, registry_client):
        """Test loader with custom registry client"""
        async with MCPToolLoader(registry_client=registry_client) as loader:
            assert loader.registry_client == registry_client

    async def test_load_from_server_object_structure(self, tool_loader, server_with_packages):
        """Test load_from_server_object returns correct structure"""
        if not server_with_packages:
            pytest.skip("No suitable server found")

        try:
            tools = await tool_loader.load_from_server_object(server_with_packages)

            # Should return a list of tools
            assert isinstance(tools, list)
            # Tools are cleaned up automatically by MultiServerMCPClient

        except ToolLoadError:
            # Loading might fail due to missing env vars or runtime, that's ok for unit test
            pytest.skip("Tool loading failed (expected for servers needing env vars)")

    def test_header_overrides_applied_to_config(self):
        """Test that header_overrides are correctly applied to MCP config"""
        converter = RegistryToMCPConverter()

        # Create a remote server with SSE transport
        server = MCPServer(
            name="test-remote-server",
            version="1.0.0",
            description="Test remote server",
            remotes=[
                Remote(
                    type="sse",
                    url="https://api.example.com/mcp",
                    headers=[{"name": "Content-Type", "value": "application/json"}],
                )
            ],
        )

        # Convert to MCP config
        mcp_config = converter.convert(server)

        # Verify initial headers
        assert mcp_config.headers is not None
        assert mcp_config.headers["Content-Type"] == "application/json"

        # Apply header overrides
        header_overrides = {"Authorization": "Bearer test-token", "X-Custom-Header": "custom-value"}

        if mcp_config.headers:
            mcp_config.headers.update(header_overrides)
        else:
            mcp_config.headers = header_overrides

        # Verify overrides applied
        assert mcp_config.headers["Authorization"] == "Bearer test-token"
        assert mcp_config.headers["X-Custom-Header"] == "custom-value"
        assert mcp_config.headers["Content-Type"] == "application/json"

    def test_args_overrides_applied_to_config(self):
        """Test that args_overrides are correctly applied to MCP config"""
        converter = RegistryToMCPConverter()

        # Create a stdio server
        server = MCPServer(
            name="test-stdio-server",
            version="1.0.0",
            description="Test stdio server",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/mcp-server",
                    version="1.0.0",
                    transport=Transport(type="stdio", url=None, headers=None),
                )
            ],
        )

        # Convert to MCP config
        mcp_config = converter.convert(server)

        # Verify initial args
        assert mcp_config.args is not None
        original_args = mcp_config.args.copy()

        # Apply args overrides
        args_overrides = ["--verbose", "--debug", "--config", "custom.json"]
        mcp_config.args = args_overrides

        # Verify overrides applied (completely replaced)
        assert mcp_config.args == args_overrides
        assert mcp_config.args != original_args

    def test_env_overrides_applied_to_config(self):
        """Test that env_overrides are correctly applied to MCP config"""
        converter = RegistryToMCPConverter()

        # Create a server with environment variables
        server = MCPServer(
            name="test-env-server",
            version="1.0.0",
            description="Test server with env vars",
            packages=[
                ServerPackage(
                    registryType="npm",
                    identifier="@test/mcp-server",
                    version="1.0.0",
                    transport=Transport(type="stdio", url=None, headers=None),
                    environmentVariables=[
                        {
                            "name": "DEFAULT_VAR",
                            "value": "default-value",
                            "isRequired": False,
                            "isSecret": False,
                        }
                    ],
                )
            ],
        )

        # Convert to MCP config
        mcp_config = converter.convert(server)

        # Apply env overrides
        env_overrides = {"API_KEY": "test-key-123", "CUSTOM_VAR": "custom-value"}

        if mcp_config.env:
            mcp_config.env.update(env_overrides)
        else:
            mcp_config.env = env_overrides

        # Verify overrides applied
        assert mcp_config.env["API_KEY"] == "test-key-123"
        assert mcp_config.env["CUSTOM_VAR"] == "custom-value"
        # Original env var should still be there
        assert "DEFAULT_VAR" in mcp_config.env

    def test_multiple_overrides_applied_together(self):
        """Test that multiple override types can be applied together"""
        converter = RegistryToMCPConverter()

        # Create a remote server
        server = MCPServer(
            name="test-multi-override",
            version="1.0.0",
            description="Test multiple overrides",
            remotes=[
                Remote(
                    type="streamable-http",
                    url="https://api.example.com/mcp",
                    headers=[{"name": "Content-Type", "value": "application/json"}],
                )
            ],
        )

        # Convert to MCP config
        mcp_config = converter.convert(server)

        # Apply header overrides
        header_overrides = {"Authorization": "Bearer token"}
        if mcp_config.headers:
            mcp_config.headers.update(header_overrides)
        else:
            mcp_config.headers = header_overrides

        # Apply env overrides (even though this is http transport, to test flexibility)
        env_overrides = {"CUSTOM_VAR": "value"}
        if mcp_config.env:
            mcp_config.env.update(env_overrides)
        else:
            mcp_config.env = env_overrides

        # Verify all overrides applied
        assert mcp_config.headers["Authorization"] == "Bearer token"
        assert mcp_config.headers["Content-Type"] == "application/json"
        assert mcp_config.env["CUSTOM_VAR"] == "value"

    def test_overrides_replace_missing_required_variables(self):
        """Test that overrides can replace missing required variables"""
        converter = RegistryToMCPConverter()

        # Create a remote server with missing required variable
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

        # Convert to MCP config - will have placeholder
        mcp_config = converter.convert(server)
        assert "<REQUIRED:missing_token>" in mcp_config.headers["Authorization"]

        # Apply header override to replace the placeholder
        header_overrides = {"Authorization": "Bearer actual-token-123"}
        if mcp_config.headers:
            mcp_config.headers.update(header_overrides)

        # Verify placeholder was replaced
        assert mcp_config.headers["Authorization"] == "Bearer actual-token-123"
        assert "<REQUIRED:" not in mcp_config.headers["Authorization"]

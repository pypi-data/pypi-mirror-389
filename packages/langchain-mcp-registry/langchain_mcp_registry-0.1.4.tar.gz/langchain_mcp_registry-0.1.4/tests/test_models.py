"""
Unit tests for Pydantic models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from langchain_mcp_registry.models import (
    MCPServer,
    ServerPackage,
    Transport,
    ServerMetadata,
    MCPConfig,
    Repository,
    ArgumentInput,
)


@pytest.mark.unit
class TestPydanticModels:
    """Test Pydantic data models"""

    def test_mcp_server_minimal(self):
        """Test MCPServer with minimal data"""
        server = MCPServer(name="test-server", version="1.0.0")
        assert server.name == "test-server"
        assert server.version == "1.0.0"

    def test_mcp_server_full(self):
        """Test MCPServer with full data"""
        server = MCPServer(
            name="test-server",
            title="Test Server",
            description="A test server",
            version="1.0.0",
            packages=[
                ServerPackage(
                    registryType="npm", identifier="@test/server", transport=Transport(type="stdio")
                )
            ],
        )
        assert server.name == "test-server"
        assert server.title == "Test Server"
        assert server.description == "A test server"
        assert len(server.packages) == 1

    def test_mcp_server_get_display_name(self):
        """Test get_display_name method"""
        # With title
        server1 = MCPServer(name="test", version="1.0", title="Test Server")
        assert server1.get_display_name() == "Test Server"

        # Without title
        server2 = MCPServer(name="test", version="1.0")
        assert server2.get_display_name() == "test"

    def test_mcp_server_get_primary_package(self):
        """Test get_primary_package method"""
        package = ServerPackage(
            registryType="npm", identifier="@test/server", transport=Transport(type="stdio")
        )

        server = MCPServer(name="test", version="1.0", packages=[package])

        assert server.get_primary_package() == package

        # Server without packages
        server_no_pkg = MCPServer(name="test", version="1.0")
        assert server_no_pkg.get_primary_package() is None

    def test_mcp_server_is_official(self):
        """Test is_official method"""
        # With active metadata
        server1 = MCPServer(
            name="test",
            version="1.0",
            metadata=ServerMetadata(
                status="active", publishedAt=datetime.now(), updatedAt=datetime.now(), isLatest=True
            ),
        )
        assert server1.is_official() is True

        # Without metadata
        server2 = MCPServer(name="test", version="1.0")
        assert server2.is_official() is False

    def test_server_package_minimal(self):
        """Test ServerPackage with minimal data"""
        package = ServerPackage(
            registryType="npm", identifier="@test/package", transport=Transport(type="stdio")
        )
        assert package.registry_type == "npm"
        assert package.identifier == "@test/package"
        assert package.transport.type == "stdio"

    def test_server_package_with_env_vars(self):
        """Test ServerPackage with environment variables"""
        package = ServerPackage(
            registryType="npm",
            identifier="@test/package",
            transport=Transport(type="stdio"),
            environmentVariables=[
                ArgumentInput(name="API_KEY", description="API Key", isRequired=True, isSecret=True)
            ],
        )
        assert len(package.environment_variables) == 1
        assert package.environment_variables[0].name == "API_KEY"
        assert package.environment_variables[0].is_required is True

    def test_mcp_config(self):
        """Test MCPConfig model"""
        config = MCPConfig(
            command="npx", args=["-y", "@test/package"], transport="stdio", timeout=30
        )
        assert config.command == "npx"
        assert len(config.args) == 2
        assert config.transport == "stdio"
        assert config.timeout == 30

    def test_mcp_config_with_env(self):
        """Test MCPConfig with environment variables"""
        config = MCPConfig(
            command="npx", args=["@test/package"], env={"API_KEY": "test-key"}, transport="stdio"
        )
        assert config.env["API_KEY"] == "test-key"

    def test_server_metadata(self):
        """Test ServerMetadata model"""
        now = datetime.now()
        metadata = ServerMetadata(status="active", publishedAt=now, updatedAt=now, isLatest=True)
        assert metadata.status == "active"
        assert metadata.is_latest is True

    def test_argument_input(self):
        """Test ArgumentInput model"""
        arg = ArgumentInput(
            name="test_arg",
            description="Test argument",
            isRequired=True,
            isSecret=False,
            default="default_value",
        )
        assert arg.name == "test_arg"
        assert arg.is_required is True
        assert arg.is_secret is False
        assert arg.default == "default_value"

    def test_model_validation_missing_required_fields(self):
        """Test that validation fails for missing required fields"""
        with pytest.raises(ValidationError):
            MCPServer()  # Missing name and version

    def test_model_field_aliases(self):
        """Test that field aliases work correctly"""
        # Test registryType alias
        package = ServerPackage(
            registryType="npm",  # Using camelCase
            identifier="test",
            transport=Transport(type="stdio"),
        )
        assert package.registry_type == "npm"  # Accessed via snake_case

        # Test metadata aliases
        now = datetime.now()
        metadata = ServerMetadata(
            status="active", publishedAt=now, updatedAt=now, isLatest=True  # camelCase
        )
        assert metadata.published_at == now  # snake_case
        assert metadata.is_latest is True

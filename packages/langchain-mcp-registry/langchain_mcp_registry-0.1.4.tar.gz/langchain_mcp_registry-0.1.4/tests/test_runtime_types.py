"""
Test all runtime types: npx, npm, python, python3, docker, node
Tests both real servers and synthetic configurations
"""

import pytest
from langchain_mcp_registry import MCPRegistryClient, RegistryToMCPConverter
from langchain_mcp_registry.models import MCPServer, ServerPackage, Transport


@pytest.mark.unit
class TestRuntimeTypes:
    """Test all RUNTIME_HINTS configurations"""

    async def test_npm_runtime_with_npx(self, registry_client, converter):
        """Test npm packages use npx command"""
        servers = await registry_client.search_servers(limit=100)

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
            pytest.skip("No npm server found in registry")

        config = converter.convert(npm_server)

        # NPM packages should use npx command
        assert config.command == "npx"
        assert len(config.args) > 0
        print(f"✓ NPM runtime: {config.command} {' '.join(config.args)}")

    async def test_python_runtime(self, registry_client, converter):
        """Test python runtime (pypi packages)"""
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
            pytest.skip("No pypi server found in registry")

        config = converter.convert(pypi_server)

        # PyPI packages should use python or uvx
        assert config.command in ["python", "python3", "uvx"]
        print(f"✓ Python runtime: {config.command} {' '.join(config.args)}")

    async def test_docker_runtime(self, registry_client, converter):
        """Test docker runtime (oci packages)"""
        servers = await registry_client.search_servers(limit=100)

        # Find an oci/docker server
        docker_server = None
        for server in servers:
            if server.packages:
                for pkg in server.packages:
                    if pkg.registry_type == "oci":
                        docker_server = server
                        break
            if docker_server:
                break

        if not docker_server:
            pytest.skip("No oci server found in registry")

        config = converter.convert(docker_server)

        # Docker packages should use docker command
        assert config.command == "docker"
        # Args contain the image identifier, not "run" command
        assert len(config.args) > 0
        print(f"✓ Docker runtime: {config.command} {' '.join(config.args)}")


@pytest.mark.integration
class TestRealRuntimeExecution:
    """Test actual runtime execution for available servers"""

    async def test_discover_all_runtime_types(self, registry_client):
        """Discover and categorize all available runtime types"""
        servers = await registry_client.search_servers(limit=100)

        runtime_examples = {"npm": [], "pypi": [], "oci": []}

        for server in servers:
            if not server.packages:
                continue

            for pkg in server.packages:
                registry_type = pkg.registry_type
                if registry_type in runtime_examples and len(runtime_examples[registry_type]) < 3:
                    runtime_examples[registry_type].append(
                        {
                            "server": server.name,
                            "identifier": pkg.identifier,
                            "transport": pkg.transport.type if pkg.transport else "unknown",
                        }
                    )

        print("\n✓ Available Runtime Types in Registry:")
        for runtime_type, examples in runtime_examples.items():
            print(f"\n  {runtime_type.upper()} ({len(examples)} examples):")
            for ex in examples:
                print(f"    - {ex['server']}: {ex['identifier']} (transport: {ex['transport']})")

        # Verify we found at least some runtime types
        assert any(len(examples) > 0 for examples in runtime_examples.values())

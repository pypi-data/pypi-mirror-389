"""
Tool Loader - Loads MCP servers from registry as LangChain tools

Refactored to use MultiServerMCPClient for simplified implementation.
"""

import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from langchain_mcp_registry.client import MCPRegistryClient
from langchain_mcp_registry.converter import RegistryToMCPConverter
from langchain_mcp_registry.exceptions import ServerNotFoundError, ToolLoadError
from langchain_mcp_registry.models import MCPServer

logger = logging.getLogger(__name__)


class MCPToolLoader:
    """
    Loads MCP tools from registry using MultiServerMCPClient

    This class provides a simplified interface to load MCP servers from the registry
    and convert them to LangChain-compatible tools using MultiServerMCPClient.

    Example:
        async with MCPToolLoader() as loader:
            # Load single server
            tools = await loader.load_from_registry("server-brave-search")

            # Load multiple servers
            tools = await loader.load_multiple(["server1", "server2"])

            # Search and load
            tools = await loader.search_and_load("weather", max_servers=3)
    """

    def __init__(
        self,
        registry_client: MCPRegistryClient | None = None,
        converter: RegistryToMCPConverter | None = None,
    ):
        """
        Initialize tool loader

        Args:
            registry_client: Custom registry client (creates default if None)
            converter: Custom converter (creates default if None)
        """
        self.registry_client = registry_client
        self.converter = converter or RegistryToMCPConverter()
        self._owned_client = registry_client is None

    async def __aenter__(self):
        """Async context manager entry"""
        if self._owned_client:
            self.registry_client = MCPRegistryClient()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._owned_client and self.registry_client:
            await self.registry_client.close()

    def _apply_overrides(
        self,
        config_dict: dict[str, Any],
        env_overrides: dict[str, str] | None = None,
        header_overrides: dict[str, str] | None = None,
        args_overrides: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Apply overrides to a config dict

        Args:
            config_dict: MCP config as dict
            env_overrides: Environment variable overrides
            header_overrides: HTTP header overrides
            args_overrides: Command arguments overrides

        Returns:
            Updated config dict
        """
        # Apply env overrides
        if env_overrides:
            if "env" in config_dict:
                config_dict["env"].update(env_overrides)
            else:
                config_dict["env"] = env_overrides

        # Apply header overrides
        if header_overrides:
            if "headers" in config_dict:
                config_dict["headers"].update(header_overrides)
            else:
                config_dict["headers"] = header_overrides

        # Apply args overrides (complete replacement)
        if args_overrides:
            config_dict["args"] = args_overrides

        return config_dict

    async def load_from_registry(
        self,
        server_name: str,
        version: str = "latest",
        env_overrides: dict[str, str] | None = None,
        header_overrides: dict[str, str] | None = None,
        args_overrides: list[str] | None = None,
    ) -> list[Any]:
        """
        Load tools from a single registry server

        Args:
            server_name: Server name (e.g., "io.github.brave/brave-search-mcp-server")
            version: Server version (default: "latest")
            env_overrides: Environment variable overrides (stdio transport)
            header_overrides: HTTP header overrides (http/sse transport)
            args_overrides: Command arguments overrides (stdio transport)

        Returns:
            List of LangChain tools

        Raises:
            ServerNotFoundError: If server not found in registry
            ToolLoadError: If tool loading fails

        Example:
            async with MCPToolLoader() as loader:
                # Load with environment overrides
                tools = await loader.load_from_registry(
                    "server-brave-search",
                    env_overrides={"API_KEY": "my-key"}
                )

                # Load remote server with header overrides
                tools = await loader.load_from_registry(
                    "remote-api-server",
                    header_overrides={"Authorization": "Bearer token123"}
                )
        """
        if not self.registry_client:
            raise RuntimeError("Registry client not initialized. Use async context manager.")

        try:
            # Get server details from registry
            logger.info(f"Fetching server '{server_name}@{version}' from registry")
            server = await self.registry_client.get_server_details(server_name, version)

            # Convert to MCP config
            mcp_config = self.converter.convert(server)

            # Convert to dict and apply overrides
            config_dict = mcp_config.dict(exclude_none=True)
            config_dict = self._apply_overrides(
                config_dict, env_overrides, header_overrides, args_overrides
            )

            # Create MultiServerMCPClient with single server
            client = MultiServerMCPClient({server.name: config_dict})

            # Get all tools
            tools = await client.get_tools()

            logger.info(f"Successfully loaded {len(tools)} tools from '{server.name}'")
            return tools

        except ServerNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to load tools from '{server_name}': {str(e)}")
            raise ToolLoadError(server_name, e)

    async def load_multiple(
        self,
        server_names: list[str],
        version: str = "latest",
        env_overrides: dict[str, dict[str, str]] | None = None,
        header_overrides: dict[str, dict[str, str]] | None = None,
        args_overrides: dict[str, list[str]] | None = None,
    ) -> list[Any]:
        """
        Load tools from multiple registry servers concurrently

        Args:
            server_names: List of server names
            version: Version for all servers (default: "latest")
            env_overrides: Per-server environment overrides
                          e.g., {"server1": {"API_KEY": "xxx"}}
            header_overrides: Per-server header overrides
                             e.g., {"server1": {"Authorization": "Bearer token"}}
            args_overrides: Per-server args overrides
                           e.g., {"server1": ["--verbose", "--debug"]}

        Returns:
            Combined list of all tools from all servers

        Example:
            async with MCPToolLoader() as loader:
                tools = await loader.load_multiple(
                    ["server-brave-search", "server-github"],
                    env_overrides={
                        "server-brave-search": {"API_KEY": "xxx"}
                    },
                    header_overrides={
                        "remote-api-server": {"Authorization": "Bearer token"}
                    }
                )
        """
        if not self.registry_client:
            raise RuntimeError("Registry client not initialized. Use async context manager.")

        logger.info(f"Loading {len(server_names)} servers from registry")

        try:
            # Fetch all server details concurrently
            import asyncio

            servers = await asyncio.gather(
                *[self.registry_client.get_server_details(name, version) for name in server_names]
            )

            # Build MultiServerMCPClient config
            server_configs = {}
            for server in servers:
                # Convert to MCP config
                mcp_config = self.converter.convert(server)
                config_dict = mcp_config.dict(exclude_none=True)

                # Apply per-server overrides
                server_env = env_overrides.get(server.name) if env_overrides else None
                server_headers = header_overrides.get(server.name) if header_overrides else None
                server_args = args_overrides.get(server.name) if args_overrides else None

                config_dict = self._apply_overrides(
                    config_dict, server_env, server_headers, server_args
                )

                server_configs[server.name] = config_dict

            # Create MultiServerMCPClient with all servers
            client = MultiServerMCPClient(server_configs)

            # Get all tools (automatically aggregated)
            tools = await client.get_tools()

            logger.info(f"Successfully loaded {len(tools)} tools from {len(servers)} servers")

            return tools

        except Exception as e:
            logger.error(f"Failed to load multiple servers: {str(e)}")
            raise ToolLoadError("multiple servers", e)

    async def search_and_load(
        self,
        query: str,
        max_servers: int = 5,
        env_overrides: dict[str, dict[str, str]] | None = None,
        header_overrides: dict[str, dict[str, str]] | None = None,
        args_overrides: dict[str, list[str]] | None = None,
    ) -> list[Any]:
        """
        Search registry and load tools from matching servers

        Args:
            query: Search query
            max_servers: Maximum number of servers to load
            env_overrides: Per-server environment overrides
            header_overrides: Per-server header overrides
            args_overrides: Per-server args overrides

        Returns:
            Combined list of all tools from matching servers

        Example:
            # Search for weather-related servers and load their tools
            tools = await loader.search_and_load(
                "weather",
                max_servers=3,
                env_overrides={
                    "weather-server": {"API_KEY": "xxx"}
                }
            )
        """
        if not self.registry_client:
            raise RuntimeError("Registry client not initialized. Use async context manager.")

        # Search for servers
        servers = await self.registry_client.search_servers(
            query=query, limit=max_servers * 2  # Get more results to filter
        )

        if not servers:
            logger.warning(f"No servers found for query: '{query}'")
            return []

        # Take only max_servers
        servers_to_load = servers[:max_servers]
        server_names = [s.name for s in servers_to_load]

        logger.info(
            f"Found {len(servers)} servers for '{query}', "
            f"loading top {len(server_names)}: {server_names}"
        )

        # Load tools from selected servers
        return await self.load_multiple(
            server_names,
            env_overrides=env_overrides,
            header_overrides=header_overrides,
            args_overrides=args_overrides,
        )

    async def load_from_server_object(
        self,
        server: MCPServer,
        env_overrides: dict[str, str] | None = None,
        header_overrides: dict[str, str] | None = None,
        args_overrides: list[str] | None = None,
    ) -> list[Any]:
        """
        Load tools from an MCPServer object directly

        Useful when you already have the server object from a search.

        Args:
            server: MCPServer object
            env_overrides: Environment variable overrides (stdio transport)
            header_overrides: HTTP header overrides (http/sse transport)
            args_overrides: Command arguments overrides (stdio transport)

        Returns:
            List of LangChain tools

        Example:
            async with MCPToolLoader() as loader:
                servers = await client.search_servers("github")

                # Load stdio server with env and args overrides
                tools = await loader.load_from_server_object(
                    servers[0],
                    env_overrides={"API_KEY": "xxx"},
                    args_overrides=["--verbose"]
                )

                # Load remote server with header overrides
                tools = await loader.load_from_server_object(
                    remote_server,
                    header_overrides={"Authorization": "Bearer token"}
                )
        """
        try:
            # Convert to MCP config
            mcp_config = self.converter.convert(server)

            # Convert to dict and apply overrides
            config_dict = mcp_config.dict(exclude_none=True)
            config_dict = self._apply_overrides(
                config_dict, env_overrides, header_overrides, args_overrides
            )

            logger.info(f"Loading tools from server object: {server.name}")

            # Create MultiServerMCPClient with single server
            client = MultiServerMCPClient({server.name: config_dict})

            # Get all tools
            tools = await client.get_tools()

            logger.info(f"Successfully loaded {len(tools)} tools from '{server.name}'")
            return tools

        except Exception as e:
            logger.error(f"Failed to load tools from server object: {str(e)}")
            raise ToolLoadError(server.name, e)

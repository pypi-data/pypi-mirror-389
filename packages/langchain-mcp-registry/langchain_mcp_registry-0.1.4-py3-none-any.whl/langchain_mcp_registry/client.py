"""
MCP Registry HTTP Client - Fetches server information from registry.modelcontextprotocol.io
"""

import json
import logging
from pathlib import Path
from urllib.parse import quote

import aiofiles
import httpx
from platformdirs import user_cache_dir

from langchain_mcp_registry.exceptions import RegistryConnectionError, ServerNotFoundError
from langchain_mcp_registry.models import (
    MCPServer,
    SearchFilters,
    ServerMetadata,
)

logger = logging.getLogger(__name__)


class MCPRegistryClient:
    """
    Client for interacting with MCP Registry API

    Example:
        async with MCPRegistryClient() as client:
            servers = await client.search_servers(query="weather")
            details = await client.get_server_details("server-name", "latest")
    """

    DEFAULT_REGISTRY_URL = "https://registry.modelcontextprotocol.io/v0/servers"

    def __init__(
        self,
        registry_url: str = DEFAULT_REGISTRY_URL,
        timeout: float = 30.0,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        cache_dir: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize MCP Registry Client

        Args:
            registry_url: Registry API base URL
            timeout: Request timeout in seconds
            cache_enabled: Enable local caching
            cache_ttl: Cache TTL in seconds
            cache_dir: Cache directory (default: user cache dir)
            headers: Additional HTTP headers
        """
        self.registry_url = registry_url
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl

        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir).expanduser()
        else:
            self.cache_dir = Path(user_cache_dir("langchain-mcp-registry"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Setup HTTP client
        default_headers = {
            "User-Agent": "langchain-mcp-registry/0.1.0",
            "Accept": "application/json",
        }
        if headers:
            default_headers.update(headers)

        self.client = httpx.AsyncClient(
            timeout=timeout, follow_redirects=True, headers=default_headers
        )

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def search_servers(
        self,
        query: str | None = None,
        limit: int = 30,
        cursor: str | None = None,
        updated_since: str | None = None,
        version: str | None = None,
    ) -> list[MCPServer]:
        """
        Search for MCP servers in the registry

        Args:
            query: Search query string
            limit: Number of results per page (1-100)
            cursor: Pagination cursor
            updated_since: Filter by update time (RFC3339 format)
            version: Filter by version

        Returns:
            List of MCPServer objects

        Example:
            servers = await client.search_servers(query="github", limit=10)
        """
        filters = SearchFilters(
            query=query,
            limit=min(max(limit, 1), 100),
            cursor=cursor,
            updated_since=updated_since,
            version=version,
        )

        # Build query parameters
        params = {}
        if filters.query:
            params["search"] = filters.query
        if filters.cursor:
            params["cursor"] = filters.cursor
        if filters.limit:
            params["limit"] = filters.limit
        if filters.updated_since:
            params["updated_since"] = filters.updated_since
        if filters.version:
            params["version"] = filters.version

        try:
            logger.info(f"Searching MCP Registry: {self.registry_url} with params: {params}")
            response = await self.client.get(self.registry_url, params=params)
            response.raise_for_status()

            data = response.json()

            # Parse servers
            servers = []
            for server_data in data.get("servers", []):
                server_dict = server_data.get("server", {})
                meta_dict = server_data.get("_meta", {}).get(
                    "io.modelcontextprotocol.registry/official"
                )

                # Parse metadata
                metadata = None
                if meta_dict:
                    metadata = ServerMetadata(**meta_dict)

                # Clean repository field if URL is empty
                if "repository" in server_dict and server_dict["repository"]:
                    if not server_dict["repository"].get("url"):
                        server_dict["repository"] = None

                # Parse server
                server = MCPServer(
                    **server_dict,
                    metadata=metadata,
                )
                servers.append(server)

            logger.info(f"Found {len(servers)} servers")
            return servers

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from registry: {e.response.status_code}")
            raise RegistryConnectionError(self.registry_url, e)
        except httpx.RequestError as e:
            logger.error(f"Request error to registry: {str(e)}")
            raise RegistryConnectionError(self.registry_url, e)
        except Exception as e:
            logger.error(f"Unexpected error fetching servers: {str(e)}")
            raise RegistryConnectionError(self.registry_url, e)

    async def get_server_details(self, server_name: str, version: str = "latest") -> MCPServer:
        """
        Get detailed information about a specific server

        Args:
            server_name: Server name (e.g., "@modelcontextprotocol/server-brave-search")
            version: Server version (default: "latest")

        Returns:
            MCPServer object with full details

        Raises:
            ServerNotFoundError: If server not found in registry

        Example:
            server = await client.get_server_details("server-brave-search", "latest")
        """
        # Remove /v0/servers from base URL and build detail URL
        base_url = self.registry_url.rsplit("/servers", 1)[0]
        # URL encode the server name to handle special characters like "/"
        encoded_name = quote(server_name, safe="")
        detail_url = f"{base_url}/servers/{encoded_name}/versions/{version}"

        try:
            logger.info(f"Fetching server details: {detail_url}")
            response = await self.client.get(detail_url)
            response.raise_for_status()

            data = response.json()
            server_dict = data.get("server", {})
            meta_dict = data.get("_meta", {}).get("io.modelcontextprotocol.registry/official")

            # Parse metadata
            metadata = None
            if meta_dict:
                metadata = ServerMetadata(**meta_dict)

            server = MCPServer(**server_dict, metadata=metadata)
            logger.info(f"Successfully fetched server: {server_name}@{version}")
            return server

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Server not found: {server_name}@{version}")
                raise ServerNotFoundError(server_name, version)
            raise RegistryConnectionError(self.registry_url, e)
        except httpx.RequestError as e:
            raise RegistryConnectionError(self.registry_url, e)

    async def get_server_versions(self, server_name: str) -> list[MCPServer]:
        """
        Get all available versions of a server

        Args:
            server_name: Server name

        Returns:
            List of MCPServer objects for each version

        Example:
            versions = await client.get_server_versions("server-brave-search")
        """
        base_url = self.registry_url.rsplit("/servers", 1)[0]
        # URL encode the server name to handle special characters like "/"
        encoded_name = quote(server_name, safe="")
        versions_url = f"{base_url}/servers/{encoded_name}/versions"

        try:
            logger.info(f"Fetching server versions: {versions_url}")
            response = await self.client.get(versions_url)
            response.raise_for_status()

            data = response.json()
            servers = []

            for server_data in data.get("servers", []):
                server_dict = server_data.get("server", {})
                meta_dict = server_data.get("_meta", {}).get(
                    "io.modelcontextprotocol.registry/official"
                )

                metadata = None
                if meta_dict:
                    metadata = ServerMetadata(**meta_dict)

                server = MCPServer(**server_dict, metadata=metadata)
                servers.append(server)

            logger.info(f"Found {len(servers)} versions for {server_name}")
            return servers

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ServerNotFoundError(server_name)
            raise RegistryConnectionError(self.registry_url, e)
        except httpx.RequestError as e:
            raise RegistryConnectionError(self.registry_url, e)

    async def _cache_get(self, key: str) -> dict | None:
        """Get cached data"""
        if not self.cache_enabled:
            return None

        cache_file = self.cache_dir / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            async with aiofiles.open(cache_file) as f:
                content = await f.read()
                return json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to read cache: {e}")
            return None

    async def _cache_set(self, key: str, data: dict) -> None:
        """Set cached data"""
        if not self.cache_enabled:
            return

        cache_file = self.cache_dir / f"{key}.json"
        try:
            async with aiofiles.open(cache_file, "w") as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to write cache: {e}")

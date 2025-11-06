"""
Configuration Converter - Transforms Registry server configs to MCP configs
"""

import logging
import os
import re

from langchain_mcp_registry.exceptions import ConfigConversionError
from langchain_mcp_registry.models import MCPConfig, MCPServer, Remote, ServerPackage

logger = logging.getLogger(__name__)


class RegistryToMCPConverter:
    """
    Converts MCP Registry server configurations to langchain-mcp-tools compatible configs

    Example:
        converter = RegistryToMCPConverter()
        mcp_config = converter.convert(registry_server)
        # Returns: {"command": "npx", "args": [...], "env": {...}}
    """

    # Runtime hint mappings
    RUNTIME_HINTS = {
        "npx": "npx",
        "npm": "npx",
        "python": "python",
        "python3": "python3",
        "uvx": "uvx",  # Astral's uv package runner (like npx for Python)
        "docker": "docker",
        "node": "node",
    }

    def __init__(self, default_timeout: int = 30):
        """
        Initialize converter

        Args:
            default_timeout: Default timeout in seconds
        """
        self.default_timeout = default_timeout

    def convert(self, server: MCPServer) -> MCPConfig:
        """
        Convert registry server to MCP configuration

        Priority: remotes > packages
        - If server has remotes (streamable-http/sse), use remote configuration
        - Otherwise, use package configuration (stdio)

        Args:
            server: MCPServer object from registry

        Returns:
            MCPConfig compatible with langchain-mcp-adapters

        Raises:
            ConfigConversionError: If conversion fails

        Example:
            config = converter.convert(server)
            # Use with langchain-mcp-adapters:
            # {"server_name": config.dict(exclude_none=True)}
        """
        try:
            # Priority 1: Check for remotes configuration (HTTP/SSE)
            if server.remotes and len(server.remotes) > 0:
                remote = server.remotes[0]  # Use first remote
                return self._convert_from_remote(server, remote)

            # Priority 2: Use package configuration (stdio)
            package = server.get_primary_package()
            if not package:
                raise ConfigConversionError(server.name, "No package or remote configuration found")

            return self._convert_from_package(server, package)

        except Exception as e:
            logger.error(f"Failed to convert server '{server.name}': {str(e)}")
            raise ConfigConversionError(server.name, str(e))

    def _get_command(self, package: ServerPackage) -> str:
        """Extract or determine the command to run"""
        # Use runtime hint if available
        if package.runtime_hint:
            hint = package.runtime_hint

            # Check if it's an absolute path to an executable (for venv Python)
            if hint.startswith("/") and ("python" in hint.lower() or "bin/" in hint):
                # For venv Python paths, check if console script exists
                if "python" in hint.lower() and "/bin/" in hint:
                    venv_dir = os.path.dirname(os.path.dirname(hint))  # Get venv dir from venv/bin/python
                    console_script = os.path.join(venv_dir, "bin", package.identifier)

                    # Check if console script exists and is executable
                    if os.path.exists(console_script) and os.access(console_script, os.X_OK):
                        logger.debug(f"Using console script: {console_script}")
                        return console_script

                logger.debug(f"Using runtime hint as full path: {hint}")
                return hint

            # Check predefined runtime hints
            hint_lower = hint.lower()
            for key, cmd in self.RUNTIME_HINTS.items():
                if key in hint_lower:
                    return cmd

        # Determine from registry type
        registry_type = package.registry_type.lower()
        if registry_type == "npm":
            return "npx"
        elif registry_type == "pypi":
            return "python"
        elif registry_type == "docker" or registry_type == "oci":
            return "docker"

        # Default to npx (most common for MCP servers)
        logger.warning(
            f"Could not determine command for {package.registry_type}, defaulting to npx"
        )
        return "npx"

    def _build_args(self, package: ServerPackage) -> list[str]:
        """Build command arguments from package configuration"""
        args = []
        registry_type = package.registry_type.lower()

        # Handle different registry types
        if registry_type == "npm":
            # For npm packages, add -y flag for auto-install
            args.append("-y")
            # Add package identifier WITHOUT version for npx
            # Note: npx with -y flag works better without @version suffix
            # as version pinning can cause tool loading issues
            args.append(package.identifier)

        elif registry_type == "pypi":
            # For Python packages, check runtime hint
            # uvx runs packages directly (no -m flag), traditional python needs -m
            if package.runtime_hint == "uvx":
                # uvx runs packages directly, no -m flag needed
                args.append(package.identifier)
            elif package.runtime_hint and package.runtime_hint.startswith("/"):
                # Check if this is a console script path or Python executable
                if package.runtime_hint.endswith(("python", "python3")):
                    # This is Python executable path - check if console script exists
                    venv_dir = os.path.dirname(os.path.dirname(package.runtime_hint))
                    console_script = os.path.join(venv_dir, "bin", package.identifier)

                    if os.path.exists(console_script) and os.access(console_script, os.X_OK):
                        # Console script exists, will be used as command - no args needed
                        logger.debug(f"Console script detected in _build_args, skipping -m flag")
                        pass
                    else:
                        # No console script, use python -m
                        args.append("-m")
                        module_name = package.identifier.replace("-", "_")
                        args.append(module_name)
                else:
                    # This is already a console script path - no args needed
                    pass
            else:
                # Traditional Python: use -m module_name
                args.append("-m")
                # Convert package name to module name (replace - with _)
                module_name = package.identifier.replace("-", "_")
                args.append(module_name)

        elif registry_type in ("docker", "oci"):
            # For Docker, just add the image identifier
            if package.version:
                args.append(f"{package.identifier}:{package.version}")
            else:
                args.append(package.identifier)

        else:
            # Default handling for unknown types
            if package.version:
                args.append(f"{package.identifier}@{package.version}")
            else:
                args.append(package.identifier)

        # Add runtime arguments
        if package.runtime_arguments:
            for arg in package.runtime_arguments:
                if arg.type == "named" and arg.name:
                    args.append(arg.name)
                    if arg.value:
                        args.append(arg.value)
                elif arg.type == "positional" and arg.value:
                    args.append(arg.value)

        # Add package arguments
        if package.package_arguments:
            for arg in package.package_arguments:
                if arg.type == "named" and arg.name:
                    args.append(arg.name)
                    if arg.value:
                        args.append(arg.value)
                elif arg.type == "positional" and arg.value:
                    args.append(arg.value)

        return args

    def _build_env(self, package: ServerPackage) -> dict[str, str] | None:
        """Build environment variables from package configuration"""
        if not package.environment_variables:
            return None

        env = {}
        for var in package.environment_variables:
            if var.name:
                # Use provided value, default, or empty string
                value = var.value or var.default or ""

                # For required secrets without values, warn user
                if var.is_secret and var.is_required and not value:
                    logger.warning(
                        f"Required secret '{var.name}' has no value. "
                        f"You must set this environment variable."
                    )
                    # Use placeholder to indicate it needs to be set
                    value = f"<REQUIRED: {var.description or var.name}>"

                env[var.name] = value

        return env if env else None

    def _convert_from_remote(self, server: MCPServer, remote: Remote) -> MCPConfig:
        """
        Convert from remote configuration (HTTP/SSE transport)

        Args:
            server: MCPServer object
            remote: Remote configuration

        Returns:
            MCPConfig for HTTP/SSE transport
        """
        # Normalize transport type
        transport_type = remote.type.lower().replace("-", "_")
        if transport_type not in ("sse", "streamable_http"):
            logger.warning(f"Unknown remote type '{remote.type}', treating as streamable_http")
            transport_type = "streamable_http"

        # Process headers with variable replacement
        headers = self._process_headers(remote.headers, remote.url)

        config = MCPConfig(
            transport=transport_type,
            url=remote.url,
            headers=headers if headers else None,
            timeout=self.default_timeout,
        )

        logger.info(
            f"Converted '{server.name}' to {transport_type} config: "
            f"url={remote.url}, headers_count={len(headers) if headers else 0}"
        )

        return config

    def _convert_from_package(self, server: MCPServer, package: ServerPackage) -> MCPConfig:
        """
        Convert from package configuration (stdio transport)

        Args:
            server: MCPServer object
            package: ServerPackage configuration

        Returns:
            MCPConfig for stdio transport
        """
        # Check if package uses HTTP/SSE transport
        if package.transport and package.transport.type in (
            "sse",
            "streamable-http",
            "streamable_http",
        ):
            return self._convert_package_http_transport(server, package)

        # Standard stdio transport
        command = self._get_command(package)
        args = self._build_args(package)
        env = self._build_env(package)

        config = MCPConfig(
            transport="stdio",
            command=command,
            args=args,
            env=env if env else None,
        )

        logger.info(
            f"Converted '{server.name}' to stdio config: command={command}, "
            f"args_count={len(args)}, env_count={len(env) if env else 0}"
        )

        return config

    def _convert_package_http_transport(
        self, server: MCPServer, package: ServerPackage
    ) -> MCPConfig:
        """
        Convert package with HTTP/SSE transport

        Args:
            server: MCPServer object
            package: ServerPackage with HTTP/SSE transport

        Returns:
            MCPConfig for HTTP/SSE transport
        """
        # Normalize transport type
        transport_type = package.transport.type.lower().replace("-", "_")

        # Get URL from transport
        url = package.transport.url
        if not url:
            raise ConfigConversionError(server.name, "HTTP/SSE transport requires URL")

        # Process headers
        headers = self._process_headers(package.transport.headers, url)

        # Add environment variables as headers if needed
        if package.environment_variables:
            if not headers:
                headers = {}
            for var in package.environment_variables:
                if var.name and not var.is_secret:
                    # Non-secret env vars can be added as headers
                    value = var.value or var.default or os.getenv(var.name, "")
                    if value:
                        headers[var.name] = value

        config = MCPConfig(
            transport=transport_type,
            url=url,
            headers=headers if headers else None,
            timeout=self.default_timeout,
        )

        logger.info(
            f"Converted '{server.name}' to {transport_type} config: "
            f"url={url}, headers_count={len(headers) if headers else 0}"
        )

        return config

    def _process_headers(
        self, headers: list[dict] | None, url: str | None = None
    ) -> dict[str, str] | None:
        """
        Process headers list from registry format to dict format

        Handles variable substitution like {token} from environment

        Args:
            headers: List of header dicts from registry
            url: Optional URL for context

        Returns:
            Dict of header name -> value, or None if no headers
        """
        if not headers:
            return None

        processed_headers = {}

        for header in headers:
            name = header.get("name")
            value = header.get("value", "")

            if not name:
                continue

            # Replace variables in value (e.g., "Bearer {token}" -> "Bearer abc123")
            if value and "{" in value:
                value = self._replace_header_variables(value, header.get("variables"))

            processed_headers[name] = value

        return processed_headers if processed_headers else None

    def _replace_header_variables(self, value: str, variables: dict | None = None) -> str:
        """
        Replace variables in header value

        Supports: {var_name} format
        Priority: 1) Provided variables 2) Environment variables

        Args:
            value: Header value template (e.g., "Bearer {token}")
            variables: Variable definitions from registry

        Returns:
            Value with variables replaced
        """
        # Find all {var} patterns
        var_pattern = r"\{(\w+)\}"
        matches = re.findall(var_pattern, value)

        for var_name in matches:
            replacement = None

            # Try to get value from variables definition
            if variables and var_name in variables:
                var_def = variables[var_name]
                # Check environment for the variable
                replacement = os.getenv(var_name.upper(), "")

                if not replacement and var_def.get("isRequired"):
                    logger.warning(
                        f"Required header variable '{var_name}' has no value. "
                        f"Set environment variable {var_name.upper()}"
                    )
                    replacement = f"<REQUIRED:{var_name}>"

            # Fall back to environment variable
            if not replacement:
                replacement = os.getenv(var_name.upper(), "")

            if replacement:
                value = value.replace(f"{{{var_name}}}", replacement)
            else:
                logger.warning(f"Header variable '{var_name}' has no value")

        return value

    def validate_config(self, config: MCPConfig) -> bool:
        """
        Validate MCP configuration

        Args:
            config: MCPConfig to validate

        Returns:
            True if valid

        Raises:
            ConfigConversionError: If validation fails
        """
        # Validate based on transport type
        if config.transport == "stdio":
            # Stdio requires command and args
            if not config.command:
                raise ConfigConversionError("unknown", "Stdio transport requires command")
            if not config.args:
                raise ConfigConversionError("unknown", "Stdio transport requires arguments")

            # Check for required environment variables with placeholders
            if config.env:
                missing_vars = [
                    key for key, value in config.env.items() if value.startswith("<REQUIRED:")
                ]
                if missing_vars:
                    logger.warning(
                        f"Configuration has {len(missing_vars)} required "
                        f"environment variables that need to be set: {missing_vars}"
                    )

        elif config.transport in ("sse", "streamable_http"):
            # HTTP/SSE requires URL
            if not config.url:
                raise ConfigConversionError("unknown", f"{config.transport} transport requires URL")

            # Check for required headers with placeholders
            if config.headers:
                missing_headers = [
                    key for key, value in config.headers.items() if "<REQUIRED:" in value
                ]
                if missing_headers:
                    logger.warning(
                        f"Configuration has {len(missing_headers)} required "
                        f"header variables that need to be set: {missing_headers}"
                    )

            # Validate timeout
            if config.timeout and config.timeout < 0:
                raise ConfigConversionError("unknown", "Timeout must be positive")

        return True

    def convert_multiple(self, servers: list[MCPServer]) -> dict[str, MCPConfig]:
        """
        Convert multiple servers to MCP configs

        Args:
            servers: List of MCPServer objects

        Returns:
            Dict mapping server names to MCPConfig objects

        Example:
            servers = await client.search_servers(query="weather")
            configs = converter.convert_multiple(servers)
            # Returns: {"server1": MCPConfig(...), "server2": MCPConfig(...)}
        """
        configs = {}
        for server in servers:
            try:
                config = self.convert(server)
                # Use server name as key (clean version)
                key = server.name.replace("@", "").replace("/", "-")
                configs[key] = config
            except ConfigConversionError as e:
                logger.error(f"Skipping server '{server.name}': {e}")
                continue

        logger.info(f"Converted {len(configs)}/{len(servers)} servers successfully")
        return configs

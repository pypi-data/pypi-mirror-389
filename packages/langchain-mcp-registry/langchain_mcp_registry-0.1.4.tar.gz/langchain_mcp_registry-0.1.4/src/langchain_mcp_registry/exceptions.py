"""
Custom exceptions for langchain-mcp-registry
"""


class MCPRegistryError(Exception):
    """Base exception for all MCP Registry errors"""

    pass


class ServerNotFoundError(MCPRegistryError):
    """Server not found in registry"""

    def __init__(self, server_name: str, version: str = "latest"):
        self.server_name = server_name
        self.version = version
        super().__init__(f"Server '{server_name}@{version}' not found in registry")


class InvalidConfigError(MCPRegistryError):
    """Invalid server configuration"""

    def __init__(self, message: str, details: dict = None):
        self.details = details or {}
        super().__init__(message)


class RegistryConnectionError(MCPRegistryError):
    """Failed to connect to registry"""

    def __init__(self, url: str, original_error: Exception = None):
        self.url = url
        self.original_error = original_error
        message = f"Failed to connect to registry at {url}"
        if original_error:
            message += f": {str(original_error)}"
        super().__init__(message)


class ToolLoadError(MCPRegistryError):
    """Failed to load tools from server"""

    def __init__(self, server_name: str, error: Exception):
        self.server_name = server_name
        self.error = error
        super().__init__(f"Failed to load tools from '{server_name}': {str(error)}")


class ConfigConversionError(MCPRegistryError):
    """Failed to convert registry config to MCP config"""

    def __init__(self, server_name: str, reason: str):
        self.server_name = server_name
        self.reason = reason
        super().__init__(f"Failed to convert config for '{server_name}': {reason}")

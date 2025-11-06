"""
Pydantic models for MCP Registry data structures
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator


class Icon(BaseModel):
    """MCP Server Icon"""

    src: HttpUrl = Field(..., description="Icon URL (must be HTTPS)")
    mime_type: str | None = Field(
        None,
        alias="mimeType",
        description="MIME type (image/png, image/svg+xml, etc.)",
    )
    sizes: list[str] | None = Field(None, description="Icon sizes (e.g., ['48x48', 'any'])")
    theme: Literal["light", "dark"] | None = Field(None, description="Icon theme")


class Repository(BaseModel):
    """Server repository information"""

    url: HttpUrl | None = Field(None, description="Repository URL")
    source: str | None = Field(None, description="Repository source (github, gitlab, etc.)")
    id: str | None = Field(None, description="Repository ID")
    subfolder: str | None = Field(None, description="Subfolder path for monorepos")

    @field_validator("url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty string to None for URL validation"""
        if v == "":
            return None
        return v


class Transport(BaseModel):
    """Transport configuration"""

    type: str = Field(..., description="Transport type (stdio, http, sse)")
    url: str | None = Field(
        None, description="URL for HTTP/SSE transports (may contain template variables)"
    )
    headers: list[dict[str, Any]] | None = Field(None, description="HTTP headers")


class ArgumentInput(BaseModel):
    """Argument or environment variable configuration"""

    name: str | None = Field(None, description="Argument/variable name")
    description: str | None = Field(None, description="Description")
    is_required: bool | None = Field(None, alias="isRequired", description="Is required?")
    is_secret: bool | None = Field(None, alias="isSecret", description="Is secret?")
    default: str | None = Field(None, description="Default value")
    value: str | None = Field(None, description="Current value")
    type: Literal["positional", "named"] | None = Field(None, description="Argument type")


class ServerPackage(BaseModel):
    """MCP Server Package configuration"""

    registry_type: str = Field(
        ..., alias="registryType", description="Registry type (npm, pypi, etc.)"
    )
    identifier: str = Field(..., description="Package identifier")
    version: str | None = Field(None, description="Package version")
    runtime_hint: str | None = Field(None, alias="runtimeHint", description="Runtime hint")
    transport: Transport = Field(..., description="Transport configuration")
    environment_variables: list[ArgumentInput] | None = Field(
        None, alias="environmentVariables", description="Environment variables"
    )
    runtime_arguments: list[ArgumentInput] | None = Field(
        None, alias="runtimeArguments", description="Runtime arguments"
    )
    package_arguments: list[ArgumentInput] | None = Field(
        None, alias="packageArguments", description="Package arguments"
    )


class Remote(BaseModel):
    """Remote service configuration"""

    type: str = Field(..., description="Remote type")
    url: str = Field(..., description="Remote URL (may contain template variables)")
    headers: list[dict[str, Any]] | None = Field(None, description="HTTP headers")


class ServerMetadata(BaseModel):
    """Server metadata from registry"""

    status: str = Field(..., description="Server status (active, deprecated, deleted)")
    published_at: datetime = Field(..., alias="publishedAt", description="Published timestamp")
    updated_at: datetime = Field(..., alias="updatedAt", description="Updated timestamp")
    is_latest: bool = Field(..., alias="isLatest", description="Is latest version?")


class MCPServer(BaseModel):
    """Complete MCP Server definition from registry"""

    name: str = Field(..., description="Server name")
    title: str | None = Field(None, description="Display name")
    description: str | None = Field(None, description="Server description")
    version: str | None = Field(None, description="Server version")
    icons: list[Icon] | None = Field(None, description="Server icons")
    website_url: HttpUrl | None = Field(None, alias="websiteUrl", description="Official website")
    repository: Repository | None = Field(None, description="Repository information")
    packages: list[ServerPackage] | None = Field(None, description="Package configurations")
    remotes: list[Remote] | None = Field(None, description="Remote configurations")
    metadata: ServerMetadata | None = Field(None, description="Registry metadata")

    def get_display_name(self) -> str:
        """Get the display name (title or name)"""
        return self.title or self.name

    def get_primary_package(self) -> ServerPackage | None:
        """Get the first/primary package configuration"""
        return self.packages[0] if self.packages else None

    def is_official(self) -> bool:
        """Check if this is an official MCP server"""
        return self.metadata is not None and self.metadata.status == "active"


class MCPConfig(BaseModel):
    """MCP server configuration for langchain-mcp-adapters

    This model represents MCP server connection configuration that will be converted
    to langchain-mcp-adapters Connection format (StdioConnection, SSEConnection, etc.).

    Note: Field support varies by transport type:
    - stdio: command, args, env, cwd
    - sse/streamable_http: url, headers, timeout
    """

    # Common fields
    transport: str = Field(
        default="stdio", description="Transport type (stdio, sse, streamable_http)"
    )

    # Stdio-specific fields
    command: str | None = Field(None, description="Command to run (stdio only)")
    args: list[str] | None = Field(None, description="Command arguments (stdio only)")
    env: dict[str, str] | None = Field(None, description="Environment variables (stdio only)")
    cwd: str | None = Field(None, description="Working directory (stdio only)")

    # HTTP/SSE-specific fields
    url: str | None = Field(None, description="Server URL (http/sse only)")
    headers: dict[str, str] | None = Field(None, description="HTTP headers (http/sse only)")
    timeout: int | None = Field(None, description="Timeout in seconds (http/sse only)")


class SearchFilters(BaseModel):
    """Search filters for registry queries"""

    query: str | None = Field(None, description="Search query string")
    cursor: str | None = Field(None, description="Pagination cursor")
    limit: int = Field(default=30, ge=1, le=100, description="Results per page")
    updated_since: str | None = Field(None, description="Filter by update time (RFC3339)")
    version: str | None = Field(None, description="Filter by version")


class RegistryResponse(BaseModel):
    """Response from MCP Registry API"""

    servers: list[MCPServer] = Field(..., description="List of servers")
    next_cursor: str | None = Field(None, alias="nextCursor", description="Next page cursor")
    count: int = Field(..., description="Total count")

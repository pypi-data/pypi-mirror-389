"""
CLI for MCP Registry operations
"""

import asyncio
import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from langchain_mcp_registry import (
    MCPRegistryClient,
    MCPToolLoader,
    RegistryToMCPConverter,
)
from langchain_mcp_registry.exceptions import MCPRegistryError, ServerNotFoundError

app = typer.Typer(
    name="mcp-registry",
    help="LangChain MCP Registry CLI - Discover and manage MCP servers",
    add_completion=False,
)
console = Console()


@app.command()
def search(
    query: str | None = typer.Argument(None, help="Search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of results"),
    show_details: bool = typer.Option(False, "--details", "-d", help="Show full details"),
):
    """
    Search for MCP servers in the registry

    Example:
        mcp-registry search weather
        mcp-registry search github --limit 5
        mcp-registry search --details
    """
    asyncio.run(_search(query, limit, show_details))


async def _search(query: str | None, limit: int, show_details: bool):
    """Async search implementation"""
    async with MCPRegistryClient() as client:
        try:
            with console.status(
                f"[bold green]Searching registry{f' for {query}' if query else ''}..."
            ):
                servers = await client.search_servers(query=query, limit=limit)

            if not servers:
                console.print("[yellow]No servers found.[/yellow]")
                return

            # Create results table
            table = Table(title=f"Found {len(servers)} MCP Servers", show_header=True)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Version", style="green")
            table.add_column("Description", style="white")
            table.add_column("Official", style="magenta")

            for server in servers:
                table.add_row(
                    server.get_display_name(),
                    server.version or "N/A",
                    (
                        (server.description[:60] + "...")
                        if server.description and len(server.description) > 60
                        else (server.description or "")
                    ),
                    "✓" if server.is_official() else "",
                )

            console.print(table)

            if show_details:
                console.print("\n[bold]Server Details:[/bold]")
                for server in servers:
                    _print_server_details(server)

        except MCPRegistryError as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def info(
    server_name: str = typer.Argument(..., help="Server name"),
    version: str = typer.Option("latest", "--version", "-v", help="Server version"),
):
    """
    Get detailed information about a specific server

    Example:
        mcp-registry info @modelcontextprotocol/server-brave-search
        mcp-registry info server-github --version 1.0.0
    """
    asyncio.run(_info(server_name, version))


async def _info(server_name: str, version: str):
    """Async info implementation"""
    async with MCPRegistryClient() as client:
        try:
            with console.status("[bold green]Fetching server info..."):
                server = await client.get_server_details(server_name, version)

            _print_server_details(server)

        except ServerNotFoundError as e:
            console.print(f"[red]Server not found: {str(e)}[/red]")
            raise typer.Exit(1)
        except MCPRegistryError as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def config(
    server_name: str = typer.Argument(..., help="Server name"),
    version: str = typer.Option("latest", "--version", "-v", help="Server version"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
):
    """
    Generate MCP configuration for a server

    Example:
        mcp-registry config server-brave-search
        mcp-registry config server-github --output github-config.json
    """
    asyncio.run(_config(server_name, version, output))


async def _config(server_name: str, version: str, output: str | None):
    """Async config implementation"""
    async with MCPRegistryClient() as client:
        try:
            with console.status("[bold green]Generating configuration..."):
                server = await client.get_server_details(server_name, version)
                converter = RegistryToMCPConverter()
                mcp_config = converter.convert(server)

            config_dict = mcp_config.dict(exclude_none=True)

            if output:
                with open(output, "w") as f:
                    json.dump(config_dict, f, indent=2)
                console.print(f"[green]Configuration saved to {output}[/green]")
            else:
                syntax = Syntax(json.dumps(config_dict, indent=2), "json", theme="monokai")
                console.print(Panel(syntax, title=f"MCP Configuration for {server.name}"))

        except MCPRegistryError as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def versions(
    server_name: str = typer.Argument(..., help="Server name"),
):
    """
    List all available versions of a server

    Example:
        mcp-registry versions server-brave-search
    """
    asyncio.run(_versions(server_name))


async def _versions(server_name: str):
    """Async versions implementation"""
    async with MCPRegistryClient() as client:
        try:
            with console.status("[bold green]Fetching versions..."):
                servers = await client.get_server_versions(server_name)

            if not servers:
                console.print("[yellow]No versions found.[/yellow]")
                return

            table = Table(title=f"Versions of {server_name}", show_header=True)
            table.add_column("Version", style="green")
            table.add_column("Published", style="cyan")
            table.add_column("Updated", style="yellow")
            table.add_column("Latest", style="magenta")

            for server in servers:
                if server.metadata:
                    table.add_row(
                        server.version or "N/A",
                        server.metadata.published_at.strftime("%Y-%m-%d"),
                        server.metadata.updated_at.strftime("%Y-%m-%d"),
                        "✓" if server.metadata.is_latest else "",
                    )

            console.print(table)

        except MCPRegistryError as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            raise typer.Exit(1)


@app.command()
def test(
    server_name: str = typer.Argument(..., help="Server name"),
    query: str = typer.Argument(..., help="Test query for the tool"),
    version: str = typer.Option("latest", "--version", "-v", help="Server version"),
):
    """
    Test a server by loading its tools (requires langchain-mcp-tools)

    Example:
        mcp-registry test server-brave-search "AI news"
    """
    asyncio.run(_test(server_name, query, version))


async def _test(server_name: str, query: str, version: str):
    """Async test implementation"""
    try:
        with console.status(f"[bold green]Loading server '{server_name}'..."):
            async with MCPToolLoader() as loader:
                tools, cleanup = await loader.load_from_registry(server_name, version)

        console.print(
            f"[green]✓ Successfully loaded {len(tools)} tools from '{server_name}'[/green]"
        )

        # List tools
        console.print("\n[bold]Available Tools:[/bold]")
        for i, tool in enumerate(tools, 1):
            console.print(f"  {i}. {tool.name}: {tool.description}")

        # Cleanup
        await cleanup()

    except MCPRegistryError as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {str(e)}[/red]")
        raise typer.Exit(1)


def _print_server_details(server):
    """Helper to print server details"""
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold]Name:[/bold] {server.get_display_name()}")
    if server.version:
        console.print(f"[bold]Version:[/bold] {server.version}")
    if server.description:
        console.print(f"[bold]Description:[/bold] {server.description}")
    if server.website_url:
        console.print(f"[bold]Website:[/bold] {server.website_url}")
    if server.repository:
        console.print(
            f"[bold]Repository:[/bold] {server.repository.url} ({server.repository.source})"
        )
    if server.is_official():
        console.print("[bold green]Official Server ✓[/bold green]")

    # Packages
    if server.packages:
        console.print("\n[bold]Packages:[/bold]")
        for pkg in server.packages:
            console.print(f"  - {pkg.registry_type}: {pkg.identifier}")
            if pkg.version:
                console.print(f"    Version: {pkg.version}")
            if pkg.runtime_hint:
                console.print(f"    Runtime: {pkg.runtime_hint}")

    # Metadata
    if server.metadata:
        console.print("\n[bold]Metadata:[/bold]")
        console.print(f"  Status: {server.metadata.status}")
        console.print(f"  Published: {server.metadata.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Updated: {server.metadata.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Latest: {'Yes' if server.metadata.is_latest else 'No'}")


if __name__ == "__main__":
    app()

"""
Example: Load Context7 MCP server from MCP Registry

This example shows how to load Context7 as a remote HTTP MCP server
directly from the MCP Registry.
"""

import asyncio
import os
from pathlib import Path
from langchain_mcp_registry import MCPRegistryClient, MCPToolLoader

# Custom MCP Registry URL (local server)
CUSTOM_REGISTRY_URL = "http://localhost:8080/v0.1/servers"

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment variables from {env_file}")
except ImportError:
    pass


async def load_context7_from_registry():
    """Load Context7 directly from MCP Registry"""
    print("=" * 60)
    print("Loading Context7 from MCP Registry")
    print("=" * 60)

    # Get API key from environment
    api_key = os.getenv("CONTEXT7_API_KEY")
    if not api_key:
        print("\n⚠️  Warning: CONTEXT7_API_KEY not found in environment")
        print("Please set CONTEXT7_API_KEY in your .env file")
        return

    # Create custom registry client with local server URL
    async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
        async with MCPToolLoader(registry_client=client) as loader:
            try:
                print("\n📦 Loading Context7 from registry: com.context7/context7")

                # Load tools directly from registry with header overrides
                tools = await loader.load_from_registry(
                    "com.context7/context7",
                    version="latest",
                    header_overrides={
                        "CONTEXT7_API_KEY": api_key
                    }
                )

                print(f"✅ Successfully loaded {len(tools)} tools from Context7!")

                print("\nAvailable tools:")
                for tool in tools:
                    print(f"  - {tool.name}")
                    if hasattr(tool, 'description'):
                        desc = tool.description[:80] + "..." if len(tool.description) > 80 else tool.description
                        print(f"    {desc}")

                # Test a tool (optional)
                if tools and hasattr(tools[0], 'name'):
                    print(f"\n💡 Example: You can now use these tools in your LangChain agents")
                    print(f"   Tool: {tools[0].name}")

            except Exception as e:
                print(f"✗ Error loading Context7: {e}")
                import traceback
                traceback.print_exc()


async def main():
    """Run the example"""
    await load_context7_from_registry()

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

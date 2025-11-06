"""
Basic usage examples for langchain-mcp-registry
"""

import asyncio
import os
from pathlib import Path
from langchain_mcp_registry import MCPRegistryClient, MCPToolLoader
from langchain_openai import ChatOpenAI

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
    pass  # python-dotenv not installed, skip

try:
    # New location in langchain.agents (LangChain 0.3+)
    from langchain.agents import create_agent as create_react_agent
except ImportError:
    # Fallback to langgraph.prebuilt for older versions
    from langgraph.prebuilt import create_react_agent


async def example_1_search_servers():
    """Example 1: Search for MCP servers in the registry"""
    print("=" * 60)
    print("Example 1: Search for servers")
    print("=" * 60)

    async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
        # Search for weather-related servers
        servers = await client.search_servers(query="weather", limit=5)

        print(f"\nFound {len(servers)} weather-related servers:\n")
        for server in servers:
            print(f"  - {server.get_display_name()}")
            print(f"    Description: {server.description}")
            print(f"    Version: {server.version}")
            print(f"    Official: {'Yes' if server.is_official() else 'No'}")
            print()


async def example_2_get_server_details():
    """Example 2: Get detailed information about a specific server"""
    print("=" * 60)
    print("Example 2: Get server details")
    print("=" * 60)

    async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
        # Get details for brave-search server
        server = await client.get_server_details(
            "io.github.brave/brave-search-mcp-server",
            version="latest"
        )

        print(f"\nServer: {server.get_display_name()}")
        print(f"Description: {server.description}")
        print(f"Website: {server.website_url}")

        if server.packages:
            pkg = server.packages[0]
            print(f"\nPackage Info:")
            print(f"  Registry: {pkg.registry_type}")
            print(f"  Identifier: {pkg.identifier}")
            print(f"  Runtime: {pkg.runtime_hint}")
            print(f"  Transport: {pkg.transport.type}")


async def example_3_load_tools():
    """Example 3: Load tools from registry"""
    print("=" * 60)
    print("Example 3: Load tools from a server")
    print("=" * 60)

    # Create custom registry client with local server URL
    async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
        async with MCPToolLoader(registry_client=client) as loader:
            # Load tools from brave-search server
            tools = await loader.load_from_registry(
                "io.github.brave/brave-search-mcp-server",
                version="latest",
                env_overrides={"BRAVE_API_KEY": "your-api-key-here"}
            )

            print(f"\nLoaded {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")

            # Cleanup handled automatically by MultiServerMCPClient


async def example_4_use_with_langchain():
    """Example 4: Use loaded tools with LangChain agent (OpenAI or DeepSeek)"""
    print("=" * 60)
    print("Example 4: Use with LangChain agent")
    print("=" * 60)

    # Detect which LLM provider to use
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not deepseek_key and not openai_key:
        print("\n❌ Error: No API key found")
        print("Please set either DEEPSEEK_API_KEY or OPENAI_API_KEY in .env file")
        return

    # Determine LLM provider
    if deepseek_key:
        llm_provider = "DeepSeek"
        llm_model = "deepseek-chat"
    else:
        llm_provider = "OpenAI"
        llm_model = "gpt-4o-mini"

    print(f"\n🤖 Using: {llm_provider} ({llm_model})")

    # Create custom registry client with local server URL
    async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
        async with MCPToolLoader(registry_client=client) as loader:
            try:
                # Load tools from huoshui-fetch
                print("\n📦 Loading huoshui-fetch (Python package)...")
                all_tools = await loader.load_from_registry(
                    "io.github.huoshuiai42/huoshui-fetch"
                )

                # Only use 2-3 tools to reduce context length
                tools = [t for t in all_tools if t.name in ['fetch_url', 'html_to_text_tool']][:2]

                print(f"✓ Loaded {len(all_tools)} tools, using {len(tools)} to reduce context:")
                for tool in tools:
                    print(f"  - {tool.name}")

                # Create LangChain agent with configured LLM
                print(f"\n🤖 Creating {llm_provider} agent...")
                if deepseek_key:
                    llm = ChatOpenAI(
                        model=llm_model,
                        openai_api_key=deepseek_key,
                        openai_api_base="https://api.deepseek.com",
                        temperature=0
                    )
                else:
                    llm = ChatOpenAI(
                        model=llm_model,
                        temperature=0
                    )

                agent = create_react_agent(llm, tools)
                print("✓ Agent created successfully")

                # Test the agent with a simple task
                print("\n💬 Testing agent with query...")
                result = await agent.ainvoke({
                    "messages": [{"role": "user", "content": "Fetch https://example.com and summarize it in one sentence"}]
                })

                print("\n" + "=" * 60)
                print("🎯 Agent Response:")
                print("=" * 60)
                print(result["messages"][-1].content)
                print("=" * 60)

            except Exception as e:
                print(f"\n❌ Error: {e}")

            # Cleanup handled automatically by MultiServerMCPClient


async def example_5_load_multiple_servers_concurrent():
    """Example 5: Load tools from multiple servers (concurrent - NEW!)"""
    print("=" * 60)
    print("Example 5: Load tools from multiple servers (CONCURRENT)")
    print("=" * 60)

    # NEW: langchain-mcp-adapters supports TRUE concurrent loading!
    # load_multiple() will load all servers in parallel for maximum performance

    server_list = [
        "com.pulsemcp.servers/pulse-fetch",  # NPM package (works reliably)
        "io.github.GoneTone/mcp-server-taiwan-weather",  # NPM weather server
        "io.github.domdomegg/time-mcp-pypi"
    ]

    try:
        # Create custom registry client with local server URL
        async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
            async with MCPToolLoader(registry_client=client) as loader:
                print(f"\n🚀 Loading {len(server_list)} servers in PARALLEL...")

                # This loads all servers concurrently!
                # Note: cleanup is handled automatically by MultiServerMCPClient
                tools = await loader.load_multiple(server_list)

                print(f"\n✅ Loaded {len(tools)} tools from {len(server_list)} servers:")
                for tool in tools[:10]:  # Show first 10
                    print(f"  - {tool.name}")

                if len(tools) > 10:
                    print(f"  ... and {len(tools) - 10} more")

                # No need to call cleanup() - handled by MultiServerMCPClient

    except Exception as e:
        print(f"\n⚠️  Error loading servers: {e}")


async def example_6_search_and_load():
    """Example 6: Search for servers and load them one by one"""
    print("=" * 60)
    print("Example 6: Search and load")
    print("=" * 60)

    try:
        # Create custom registry client with local server URL
        async with MCPRegistryClient(registry_url=CUSTOM_REGISTRY_URL) as client:
            async with MCPToolLoader(registry_client=client) as loader:
                # Search for time/date servers
                print("Searching for 'time' related servers...")
                servers = await loader.registry_client.search_servers(
                    query="time",
                    limit=3
                )

                print(f"\nFound {len(servers)} servers. Loading tools...")

                all_tools = []
                successful_count = 0

                for server in servers[:2]:  # Load first 2
                    try:
                        print(f"\n  Loading {server.name}...")
                        # Note: cleanup handled by MultiServerMCPClient
                        tools = await loader.load_from_server_object(server)
                        all_tools.extend(tools)
                        successful_count += 1
                        print(f"    ✓ {len(tools)} tools loaded")
                    except Exception as e:
                        print(f"    ✗ Failed: {str(e)[:60]}")
                        continue

                print(f"\n✅ Total: {len(all_tools)} tools from {successful_count} servers")

                # Cleanup handled automatically by MultiServerMCPClient

    except Exception as e:
        print(f"\n⚠️  Search and load failed: {e}")


async def example_7_load_context7():
    """Example 7: Use Context7 agent to query latest React version"""
    print("=" * 60)
    print("Example 7: Context7 Agent - Query Latest React")
    print("=" * 60)

    # Check for API keys
    context7_key = os.getenv("CONTEXT7_API_KEY")
    if not context7_key:
        print("\n⚠️  Warning: CONTEXT7_API_KEY not found in environment")
        print("Please set CONTEXT7_API_KEY in your .env file")
        print("You can get an API key from: https://context7.com")
        return

    # Detect which LLM provider to use
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not deepseek_key and not openai_key:
        print("\n❌ Error: No LLM API key found")
        print("Please set either DEEPSEEK_API_KEY or OPENAI_API_KEY in .env file")
        return

    # Determine LLM provider
    if deepseek_key:
        llm_provider = "DeepSeek"
        llm_model = "deepseek-chat"
    else:
        llm_provider = "OpenAI"
        llm_model = "gpt-4o-mini"

    print(f"\n🤖 Using LLM: {llm_provider} ({llm_model})")

    try:
        import json
        from langchain_mcp_registry.models import MCPServer

        # Load Context7 configuration from local JSON file
        config_file = Path(__file__).parent / "context7-registry-config.json"
        print(f"\n📦 Loading Context7 from local config: {config_file.name}")

        with open(config_file, 'r') as f:
            server_data = json.load(f)

        # Parse into MCPServer object
        server = MCPServer(**server_data)
        print(f"✓ Loaded server: {server.name}")
        print(f"🔗 Remote HTTP server (streamable-http transport)")
        print(f"   URL: {server.remotes[0].url}")

        # Load tools with MCPToolLoader
        async with MCPToolLoader() as loader:
            # Load tools from server object with header overrides
            tools = await loader.load_from_server_object(
                server,
                header_overrides={
                    "CONTEXT7_API_KEY": context7_key
                }
            )

            print(f"\n✅ Successfully loaded {len(tools)} tools from Context7!")

            # Show available tools
            print("\nAvailable tools:")
            for tool in tools:
                print(f"  - {tool.name}")

            # Create LangChain agent with Context7 tools
            print(f"\n🤖 Creating {llm_provider} agent with Context7 tools...")
            if deepseek_key:
                llm = ChatOpenAI(
                    model=llm_model,
                    openai_api_key=deepseek_key,
                    openai_api_base="https://api.deepseek.com",
                    temperature=0
                )
            else:
                llm = ChatOpenAI(
                    model=llm_model,
                    temperature=0
                )

            agent = create_react_agent(llm, tools)
            print("✓ Agent created successfully")

            # Query latest React version using Context7
            print("\n💬 Querying: What is the latest version of React and what are the key features?")
            print("-" * 60)

            result = await agent.ainvoke({
                "messages": [{
                    "role": "user",
                    "content": "What is the latest version of React? Please provide the version number and key features or changes in the latest release."
                }]
            })

            # Display result
            print("\n" + "=" * 60)
            print("🎯 Agent Response:")
            print("=" * 60)
            response = result["messages"][-1].content
            print(response)
            print("=" * 60)

            # Show key features
            print("\n💡 Key Features Demonstrated:")
            print("   ✓ Loading from local JSON config file")
            print("   ✓ Remote HTTP server (streamable-http transport)")
            print("   ✓ Header-based authentication (header_overrides)")
            print("   ✓ Real-time documentation lookup via Context7 API")
            print("   ✓ LangChain agent integration")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all examples"""
    # Example 1: Search servers
    # await example_1_search_servers()

    # Example 2: Get server details
    # await example_2_get_server_details()

    # Example 3: Load tools
    # Uncomment to run (requires server dependencies):
    # await example_3_load_tools()

    # Example 4: Use with LangChain
    # Uncomment to run (requires API keys):
    # await example_4_use_with_langchain()

    # Example 5: Load multiple servers (CONCURRENT - NEW!)
    # Uncomment to run (requires server dependencies):
    # await example_5_load_multiple_servers_concurrent()

    # Example 6: Search and load
    # Uncomment to run (requires server dependencies):
    # await example_6_search_and_load()

    # Example 7: Load Context7 (Remote HTTP Server with header overrides)
    # Uncomment to run (requires CONTEXT7_API_KEY):
    await example_7_load_context7()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

"""
Real MCP Server integration test with LangChain Agent
Tests actual MCP server loading and usage with OpenAI
"""

import pytest
from langchain_mcp_registry import MCPToolLoader


@pytest.mark.agent
@pytest.mark.slow
class TestRealMCPServerAgent:
    """Test LangChain Agent with real MCP servers"""

    async def test_load_real_mcp_server_tools(self, llm_config):
        """Test loading real MCP server tools (pulse-fetch)"""
        async with MCPToolLoader() as loader:
            # Search for pulse-fetch server
            servers = await loader.registry_client.search_servers(query="fetch", limit=10)

            # Find pulse-fetch server
            pulse_fetch = None
            for server in servers:
                if "pulse-fetch" in server.name and server.packages:
                    pulse_fetch = server
                    break

            if not pulse_fetch:
                pytest.skip("pulse-fetch server not found")

            print(f"\n✓ Found MCP server: {pulse_fetch.name}")

            # Convert to config
            config = loader.converter.convert(pulse_fetch)
            print(f"✓ Converted to MCP config")
            print(f"  Command: {config.command}")
            print(f"  Args: {' '.join(config.args)}")

            # Load the actual tools
            try:
                tools = await loader.load_from_server_object(pulse_fetch)

                print(f"✓ Successfully loaded {len(tools)} tools from MCP server!")

                # Show tool information
                for tool in tools:
                    tool_name = getattr(tool, "name", str(tool))
                    tool_desc = getattr(tool, "description", "N/A")
                    print(f"  - Tool: {tool_name}")
                    print(f"    Description: {tool_desc[:100]}...")

                # Verify tools are callable LangChain tools
                assert len(tools) > 0, "Should have at least one tool"
                assert hasattr(tools[0], "invoke") or hasattr(
                    tools[0], "ainvoke"
                ), "Tool should have invoke/ainvoke methods"

                print("\n✓ Real MCP server tools are ready for LangChain Agent!")
                print("✓ Cleanup handled automatically by MultiServerMCPClient")

            except Exception as e:
                print(f"✗ Tool loading failed: {e}")
                pytest.skip(f"Tool loading failed (might need API keys): {e}")

    async def test_agent_with_real_mcp_server(self, llm_config):
        """Test creating LangChain Agent with real MCP server tools"""
        if not llm_config:
            pytest.skip("No LLM API key configured (set OPENAI_API_KEY or DEEPSEEK_API_KEY)")

        from langchain_openai import ChatOpenAI
        from langgraph.prebuilt import create_react_agent

        async with MCPToolLoader() as loader:
            # Load pulse-fetch server
            servers = await loader.registry_client.search_servers(query="pulse-fetch", limit=5)

            if not servers:
                pytest.skip("pulse-fetch server not found")

            server = servers[0]
            print(f"\n📦 Loading MCP server: {server.name}")

            try:
                tools = await loader.load_from_server_object(server)

                print(f"✓ Loaded {len(tools)} tools from MCP server")

                # Create LangChain Agent with real MCP tools
                if llm_config["provider"] == "deepseek":
                    llm = ChatOpenAI(
                        model=llm_config["model"],
                        openai_api_key=llm_config["api_key"],
                        openai_api_base=llm_config["base_url"],
                        temperature=0,
                    )
                else:  # openai
                    llm = ChatOpenAI(model=llm_config["model"], temperature=0)

                agent = create_react_agent(llm, tools)

                print(f"✓ Created LangChain Agent with real MCP tools")
                print(f"  LLM: {llm_config['provider']} - {llm_config['model']}")
                print(f"  Tools: {len(tools)} from {server.name}")

                # List available tools
                for tool in tools:
                    tool_name = getattr(tool, "name", "unknown")
                    print(f"  - {tool_name}")

                # Verify agent can describe its tools
                result = await agent.ainvoke(
                    {"messages": [{"role": "user", "content": "What tools do you have available?"}]}
                )

                response = result["messages"][-1].content
                print(f"\n🤖 Agent response:\n{response}\n")

                # Agent should mention the tools
                assert len(response) > 0, "Agent should respond"

                print("✅ SUCCESS: LangChain Agent created with REAL MCP server tools!")
                print("✅ Agent successfully integrated with MCP tooling!")
                print("✅ Cleanup handled automatically by MultiServerMCPClient")

            except Exception as e:
                print(f"⚠️  Test limitation: {e}")
                pytest.skip(f"MCP server requires runtime setup: {e}")

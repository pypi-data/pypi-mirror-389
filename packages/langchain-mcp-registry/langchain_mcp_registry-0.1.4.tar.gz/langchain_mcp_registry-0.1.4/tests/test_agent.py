"""
LangChain Agent integration tests with real OpenAI API
"""

import pytest
import os
from langchain_mcp_registry import MCPToolLoader


@pytest.mark.agent
@pytest.mark.slow
class TestLangChainAgent:
    """Test integration with LangChain agents using real API"""

    async def test_llm_api_key_available(self, llm_config):
        """Test that LLM API key is available (OpenAI or DeepSeek)"""
        assert llm_config is not None, "Neither OPENAI_API_KEY nor DEEPSEEK_API_KEY is set"
        assert llm_config["api_key"] is not None, "API key is None"
        assert len(llm_config["api_key"]) > 0, "API key is empty"
        print(f"Using {llm_config['provider']} with model {llm_config['model']}")

    async def test_search_and_convert_without_loading(self, openai_api_key):
        """Test search and config conversion (without actual tool loading)"""
        async with MCPToolLoader() as loader:
            # Search for servers
            servers = await loader.registry_client.search_servers(query="fetch", limit=10)
            assert len(servers) > 0

            # Find servers that can be converted
            converted_count = 0
            for server in servers:
                if server.packages and len(server.packages) > 0:
                    try:
                        config = loader.converter.convert(server)
                        assert config.command is not None
                        assert len(config.args) > 0
                        converted_count += 1

                        if converted_count >= 5:
                            break
                    except Exception:
                        continue

            assert converted_count >= 3, "Should convert at least 3 servers"

    async def test_agent_with_mock_tools(self, llm_config):
        """Test creating agent with mock tools (proves agent creation works)"""
        if not llm_config:
            pytest.skip("No LLM API key configured (set OPENAI_API_KEY or DEEPSEEK_API_KEY)")

        from langchain_openai import ChatOpenAI
        from langgraph.prebuilt import create_react_agent
        from langchain_core.tools import tool

        # Create a simple mock tool
        @tool
        def get_weather(location: str) -> str:
            """Get weather for a location"""
            return f"Weather in {location}: Sunny, 72°F"

        @tool
        def calculate_sum(a: int, b: int) -> int:
            """Calculate sum of two numbers"""
            return a + b

        mock_tools = [get_weather, calculate_sum]

        # Create agent with configured LLM
        if llm_config["provider"] == "deepseek":
            llm = ChatOpenAI(
                model=llm_config["model"],
                openai_api_key=llm_config["api_key"],
                openai_api_base=llm_config["base_url"],
                temperature=0,
            )
        else:  # openai
            llm = ChatOpenAI(model=llm_config["model"], temperature=0)

        agent = create_react_agent(llm, mock_tools)

        assert agent is not None

        # Test simple invocation
        result = await agent.ainvoke({"messages": [{"role": "user", "content": "What is 5 + 3?"}]})

        assert result is not None
        assert "messages" in result

        # Check that the response contains the answer
        final_message = result["messages"][-1].content
        assert "8" in final_message or "eight" in final_message.lower()

    async def test_langchain_imports(self):
        """Test that required LangChain packages are available"""
        try:
            from langchain_openai import ChatOpenAI
            from langgraph.prebuilt import create_react_agent
            from langchain_core.tools import tool

            assert ChatOpenAI is not None
            assert create_react_agent is not None
            assert tool is not None

        except ImportError as e:
            pytest.fail(f"Required LangChain package not available: {e}")

    async def test_langchain_mcp_adapters_import(self):
        """Test that langchain-mcp-adapters is available"""
        try:
            from langchain_mcp_adapters.tools import load_mcp_tools
            from langchain_mcp_adapters.sessions import create_session

            assert load_mcp_tools is not None
            assert create_session is not None
        except ImportError as e:
            pytest.fail(f"langchain-mcp-adapters not available: {e}")

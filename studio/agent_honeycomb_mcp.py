from contextlib import asynccontextmanager
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent


async def make_graph():
    client = MultiServerMCPClient(
        {
            "honeycomb": {
                "disabled": False,
                "timeout": 60,
                "command": "node",
                "transport": "stdio",
                "args": ["/Users/qi.yu/Code/AIGC/honeycomb-mcp/build/index.mjs"],
                "env": {"HONEYCOMB_API_KEY": "qO8mPrbG1hTl4vAedyruoB"},
            },
        }
    )
    tools = await client.get_tools()
    agent = create_react_agent("openai:gpt-4.1", tools)
    return agent

import pytest

from weather_agent.mcp_runtime import (
    call_mcp_tool,
    connect_mcp,
    load_mcp_tools,
)


@pytest.mark.asyncio
async def test_mcp_tools_are_discovered_and_called():
    async with connect_mcp() as client:
        tools = await load_mcp_tools(client)

        names = {
            tool["function"]["name"]
            for tool in tools
        }

        assert "suggest_clothing" in names
        assert "packing_list" in names

        result = await call_mcp_tool(
            client,
            "packing_list",
            {"is_raining": True},
        )

        assert "雨伞" in result

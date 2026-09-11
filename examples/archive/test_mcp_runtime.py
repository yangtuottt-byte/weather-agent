import asyncio

from mcp_runtime import (
    call_mcp_tool,
    connect_mcp,
    load_mcp_tools,
)


async def main():
    print("正在启动 MCP 服务……")

    async with connect_mcp() as client:
        tools = await load_mcp_tools(client)

        print("已发现工具：")
        for tool in tools:
            print("-", tool["function"]["name"])

        result1 = await call_mcp_tool(
            client,
            "suggest_clothing",
            {"temperature": 28.9},
        )
        print("穿衣建议：", result1)

        result2 = await call_mcp_tool(
            client,
            "packing_list",
            {"is_raining": True},
        )
        print("物品清单：", result2)

    print("MCP 服务已关闭。")


asyncio.run(main())
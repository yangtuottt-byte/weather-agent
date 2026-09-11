import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters


async def main():
    server_path = Path(__file__).resolve().parent / "clothing_server.py"

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    print("正在启动 MCP 服务……")

    async with Client(server) as client:
        print("第一次调用：")
        result1 = await client.call_tool(
            "suggest_clothing",
            {"temperature": 28.9},
        )
        print(result1.structured_content)

        print("第二次调用：")
        result2 = await client.call_tool(
            "packing_list",
            {"is_raining": True},
        )
        print(result2.structured_content)

    print("MCP 服务已关闭。")


asyncio.run(main())
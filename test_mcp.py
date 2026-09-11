from ast import main
import asyncio
from http import server
from operator import call
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters
from pydantic import conbytes
 
async def get_clothing_advice(temperature):
    server_path = Path(__file__).resolve().parent / "clothing_server.py"

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)]
    )

    print("正在连接穿衣建议服务……")

    async with Client(server) as client:
        result = await client.call_tool(
            "suggest_clothing",
            {
                "temperature": 28.9
            },
        )
        return result.structured_content["result"]

async def call_mcp_tool(name, arguments):
    server_path = Path(__file__).resolve().parent / "clothing_server.py"

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with Client(server) as client:
        result = await client.call_tool(name, arguments)

        text_parts = []

        for content in result.content:
            if content.type == "text":
                text_parts.append(content.text)

        text = "\n".join(text_parts)

        if result.is_error:
            return f"MCP工具执行失败：{text}"

        return text


if __name__ == "__main__":
    advice = asyncio.run(get_clothing_advice(28.9))
    print("穿衣建议：", advice)

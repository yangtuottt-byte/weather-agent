import asyncio
import json
from openai.types.chat import ChatCompletionToolParam
import sys
from pathlib import Path
from mcp import Client, StdioServerParameters

async def load_mcp_tools():
    server_path = Path(__file__).resolve().parent / "clothing_server.py"

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with Client(server) as client:
        result = await client.list_tools()

        tools: list[ChatCompletionToolParam] = []

        for tool in result.tools:
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.input_schema,
                },
            })

        return tools


if __name__ == "__main__":
    tools = asyncio.run(load_mcp_tools())
    print(json.dumps(tools, ensure_ascii=False, indent=2))


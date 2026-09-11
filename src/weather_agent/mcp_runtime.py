"""Connection helpers for the local MCP server."""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import Client, StdioServerParameters


@asynccontextmanager
async def connect_mcp():
    """Start the MCP server and keep one connection open for a chat."""
    server_path = (
        Path(__file__).resolve().parent
        / "mcp_servers"
        / "clothing_server.py"
    )
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)],
    )

    async with Client(server) as client:
        yield client


async def load_mcp_tools(client) -> list[dict]:
    """Convert MCP tool definitions to the model's tool format."""
    result = await client.list_tools()
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.input_schema,
            },
        }
        for tool in result.tools
    ]


async def call_mcp_tool(client, name: str, arguments: dict) -> str:
    """Call an MCP tool and return its text output."""
    result = await client.call_tool(name, arguments)
    text = "\n".join(
        content.text
        for content in result.content
        if content.type == "text"
    )

    if result.is_error:
        return f"MCP工具执行失败：{text}"

    return text

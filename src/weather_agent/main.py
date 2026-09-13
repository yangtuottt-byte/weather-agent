"""Command-line entry point for the weather Agent."""

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .local_tools import get_today, get_weather
from .mcp_runtime import call_mcp_tool, connect_mcp, load_mcp_tools


logger = logging.getLogger(__name__)


LOCAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_today",
            "description": "获取运行程序的电脑上的今天日期。",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的当前气温，只支持北京、上海、广州。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称。",
                        "enum": ["北京", "上海", "广州"],
                    },
                },
                "required": ["city"],
            },
        },
    },
]


def create_client() -> OpenAI:
    """Load the API key and create the DeepSeek client."""
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    if not env_path.exists():
        env_path = project_root / ".venv" / ".env"
    load_dotenv(env_path)

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请在项目根目录的 .env 中设置 DEEPSEEK_API_KEY")

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )


async def execute_tool(
    name: str,
    arguments: dict,
    mcp_client,
    mcp_tool_names: set[str],
) -> str:
    """Execute one tool and turn failures into a readable tool result."""
    try:
        if name == "get_today":
            return get_today()

        if name == "get_weather":
            return get_weather(arguments["city"])

        if name in mcp_tool_names:
            return await call_mcp_tool(
                mcp_client,
                name,
                arguments,
            )

        return f"错误：未知工具 {name}"

    except Exception:
        logger.exception("工具执行失败：%s", name)
        return "工具执行失败，请稍后重试。"


async def run_agent() -> None:
    client = create_client()

    print("正在加载 MCP 工具……")
    async with connect_mcp() as mcp_client:
        mcp_tools = await load_mcp_tools(mcp_client)
        all_tools = list(LOCAL_TOOLS) + mcp_tools
        mcp_tool_names = {
            tool["function"]["name"] for tool in mcp_tools
        }
        print(
            "已加载 MCP 工具：",
            ", ".join(sorted(mcp_tool_names)),
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "你是天气助手，请用中文简短回答。"
                    "查询今天日期使用 get_today。"
                    "查询北京、上海、广州的当前气温使用 get_weather。"
                    "可以根据 MCP 工具说明使用其他工具。"
                    "不要编造天气数据。"
                ),
            },
        ]

        while True:
            task = input("\n你想问什么？输入‘退出’结束：").strip()
            if task == "退出":
                print("对话结束。")
                break
            if not task:
                continue

            messages.append({"role": "user", "content": task})

            for _ in range(6):
                response = client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=messages,
                    tools=all_tools,
                    tool_choice="auto",
                    extra_body={"thinking": {"type": "disabled"}},
                )

                message = response.choices[0].message
                messages.append(message)

                if not message.tool_calls:
                    print("模型回答：", message.content)
                    break

                for tool_call in message.tool_calls:
                    if tool_call.type != "function":
                        continue

                    name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    print("模型选择的工具：", name)
                    print("模型提供的参数：", arguments)

                    result = await execute_tool(
                        name,
                        arguments,
                        mcp_client,
                        mcp_tool_names,
                    )

                    print("工具执行结果：", result)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    })
            else:
                print("已达到最多6轮，本次问题还没有完成。")

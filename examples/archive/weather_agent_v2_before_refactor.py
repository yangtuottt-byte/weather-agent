import os
import json
import asyncio
from dotenv import load_dotenv
from openai import OpenAI
import requests
from datetime import date
from unittest import result
from pathlib import Path
from openai.types.chat import ChatCompletionToolParam
from test_mcp import get_clothing_advice
from mcp_runtime import (
    connect_mcp,
    load_mcp_tools,
    call_mcp_tool,
)

# 获取日期
def get_today():
    today = date.today()
    return today.isoformat()


# 天气
def get_weather(city):
    cities = {
        "北京": {"latitude": 39.90, "longitude": 116.40},
        "上海": {"latitude": 31.23, "longitude": 121.47},
        "广州": {"latitude": 23.13, "longitude": 113.26},
    }

    if city not in cities:
        return "目前只支持北京、上海和广州。"

    location = cities[city]

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "current": "temperature_2m",
        "temperature_unit": "celsius",
        "timezone": "Asia/Shanghai",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()

    data = response.json()
    temperature = data["current"]["temperature_2m"]

    return f"{city}当前气温：{temperature}摄氏度"


env_path = Path(__file__).resolve().parent / ".venv" / ".env"
load_dotenv(env_path)

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("请检查 .venv/.env 中是否保存了 DEEPSEEK_API_KEY")

tools:list[ChatCompletionToolParam]= [
    {
        "type": "function",
        "function": {
            "name": "get_today",
            "description": "获取运行程序的电脑上的今天日期",
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
                        "description": "城市名称",
                        "enum": ["北京", "上海", "广州"],
                    },
                },
                "required": ["city"],

            },
        },
    },
]

async def run_agent():
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    print("正在加载 MCP 工具……")

    async with connect_mcp() as mcp_client:
        mcp_tools = await load_mcp_tools(mcp_client)

        all_tools = list(tools)
        mcp_tool_names = set()

        for tool in mcp_tools:
            name = tool["function"]["name"]

            if name in {"get_today", "get_weather"}:
                raise ValueError(f"工具名称重复：{name}")

            all_tools.append(tool)
            mcp_tool_names.add(name)

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
            }
        ]

        while True:
            task = input("\n你想问什么？输入“退出”结束：").strip()

            if task == "退出":
                print("对话结束。")
                break

            if not task:
                continue

            messages.append({
                "role": "user",
                "content": task,
            })

            for step in range(6):
                response = client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=messages,
                    tools=all_tools,
                    tool_choice="auto",
                    extra_body={
                        "thinking": {
                            "type": "disabled",
                        }
                    },
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
                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print("模型选择的工具：", name)
                    print("模型提供的参数：", arguments)

                    if name == "get_today":
                        result = get_today()

                    elif name == "get_weather":
                        result = get_weather(arguments["city"])

                    elif name in mcp_tool_names:
                        result = await call_mcp_tool(
                            mcp_client,
                            name,
                            arguments,
                        )

                    else:
                        result = "错误：未知工具"

                    print("工具执行结果：", result)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    })

            else:
                print("已达到最多6轮，本次问题还没有完成。")


if __name__ == "__main__":
    asyncio.run(run_agent())
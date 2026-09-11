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
from test_mcp import call_mcp_tool
from list_mcp_tools import load_mcp_tools

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

print("正在加载 MCP 工具……")

mcp_tools = asyncio.run(load_mcp_tools())

mcp_tool_names = set()
used_names = {"get_today", "get_weather"}

for tool in mcp_tools:
    if tool["type"] == "function":
        name = tool["function"]["name"]

        if name in used_names:
            raise ValueError(f"工具名称重复：{name}")

        used_names.add(name)
        mcp_tool_names.add(name)

tools.extend(mcp_tools)

print("已加载 MCP 工具：", ", ".join(sorted(mcp_tool_names)))

# tools.append({
#     "type": "function",
#     "function": {
#         "name": "suggest_clothing",
#         "description": "根据摄氏气温给出简单穿衣建议，不考虑风雨和个人体感。",
#         "parameters": {
#             "type": "object",
#             "properities": {
#                 "temperature": {
#                     "type": "number",
#                     "description": "摄氏气温，例如28.9",
#                 },
#             },
#         },
#     }
# })

# 创建模型客户端
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
)

# task = input("你想问什么？")

messages = [
    {
        "role": "system",
        "content": ("你是天气助手，请用中文简短回答。"
                    "你可以查询今天日期、北京上海广州的当前气温，以及提供简单穿衣建议。"
                    "查询日期使用 get_today，查询气温使用 get_weather。"
                    "用户提供气温并询问穿衣建议时，使用 suggest_clothing。"
                    "查询气温但没有提供城市时，先询问城市。"
                    "用户询问某城市现在适合穿什么时，先调用 get_weather 获取气温，"
                    "再用返回的气温调用 suggest_clothing，最后根据工具结果回答。"
                    "不要编造日期和天气数据。"
                    "也可以使用工具清单中的其他工具，请根据各工具的说明判断用途。"
                    "工具所需信息不明确时，先询问用户，不要猜测。"
                    ),
    },
    # {
    #     "role": "user",
    #     "content": task,
    # },
]

while True:
    task = input("\n你想问什么？输“退出”结束").strip()

    if task == "退出":
        print("对话结束")
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
            tools=tools,
            tool_choice="auto",
            extra_body={"thinking":{"type": "disabled"}},
        )
        message = response.choices[0].message
        messages.append(message)

        if not message.tool_calls:
            print("模型回答：", message.content)
            break
        
        for tool_call in message.tool_calls:
            if tool_call.type == "function":
                name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                print("模型选择的工具：", name)
                print("模型提供的参数:", arguments)

                if name == "get_today":
                    result = get_today()
                elif name == "get_weather":
                    result = get_weather(arguments["city"])
                # elif name == "suggest_clothing":
                #     result = asyncio.run(
                #         get_clothing_advice(arguments["temperature"])
                #     )
                elif name in mcp_tool_names:
                    result = asyncio.run(
                    call_mcp_tool(name, arguments)
                )
                else:
                    result = "错误，未知工具"
                print("工具执行结果：", result)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                })
    else:
        print("已达到最多6轮，本次任务还没有完成。")
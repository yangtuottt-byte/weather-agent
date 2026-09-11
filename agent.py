import json
import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionToolParam
from openai import OpenAI, api_key


def add(a,b):
    return a + b

tools: list[ChatCompletionToolParam] = [
    {
        "type" : "function",
        "function" : {
            "name" : "add",
            "description" : "计算两个数字的和",
            "parameters": {
                "type": "object",
                "properties" : {
                    "a" : {
                        "type" : "number",
                        "description": "第一个数字",
                    },
                    "b" : {
                        "type" : "number",
                        "description": "第二个数字",
                    },
                },
                "required": ["a", "b"],
            },            
        },
    }
]
env_path = Path(__file__).resolve().parent / ".venv" / ".env"
load_dotenv(env_path)

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise ValueError("请在 .venv/.env 中设置 DEEPSEEK_API_KEY")

client = OpenAI(
    api_key = api_key,
    base_url= "https://api.deepseek.com",
    
) 

task = input("你想让我做什么？")

messages = [
        {
            "role" : "system",
            "content" : "你是一个助手，遇到两个数字相加时，请使用add工具。"
        },
        {
            "role" : "user",
            "content" : task
        }
    ]

response = client.chat.completions.create(
    model = "deepseek-v4-flash",
    messages = messages,
    tools = tools,
    extra_body = {
        "thinking": {
            "type": "disabled"
        }
    },
)
message = response.choices[0].message
if message.tool_calls:
    messages.append(message)
    for tool_call in message.tool_calls:
        if tool_call.type == "function":
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print("模型想调用的工具：", name)
            print("模型提供的参数:", arguments)

            if name == "add":
                result = add(
                    a = arguments["a"],
                    b = arguments["b"]
                )
            else:
                result = f"错误，未知工具{name}"
            print("工具执行结果:",result)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result),
            })
        print("正在把工具结果发给模型...")
        final_response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=messages,
            extra_body={"thinking": {"type": "disabled"}},
        )
        print("模型回答：", final_response.choices[0].message.content)
else:
    print("模型回答：", message.content)

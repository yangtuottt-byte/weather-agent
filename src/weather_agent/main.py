"""Command-line entry point for the weather Agent."""

import asyncio
import json
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from .local_tools import get_today, get_weather
from .history import ConversationStore, keep_last_turns
from .mcp_runtime import call_mcp_tool, connect_mcp, load_mcp_tools
from .observability import EventLogger


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure concise process logs without exposing message content."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


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


SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "你是天气助手，请用中文简短回答。"
        "查询今天日期使用 get_today。"
        "查询北京、上海、广州的当前气温使用 get_weather。"
        "可以根据 MCP 工具说明使用其他工具。"
        "不要编造天气数据。"
    ),
}


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
    event_logger: EventLogger | None = None,
) -> str:
    """Execute one tool and turn failures into a readable tool result."""
    started_at = time.perf_counter()
    logger.info("tool_start name=%s", name)
    if event_logger:
        event_logger.record("tool_started", tool_name=name)

    try:
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
            logger.warning("tool_unknown name=%s", name)
            return f"错误：未知工具 {name}"

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            "tool_success name=%s elapsed_ms=%.1f",
            name,
            elapsed_ms,
        )
        if event_logger:
            event_logger.record(
                "tool_completed",
                tool_name=name,
                elapsed_ms=round(elapsed_ms, 1),
                success=True,
            )
        return result

    except Exception:
        logger.exception("工具执行失败：%s", name)
        if event_logger:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            event_logger.record(
                "tool_completed",
                tool_name=name,
                elapsed_ms=round(elapsed_ms, 1),
                success=False,
            )
        return "工具执行失败，请稍后重试。"


async def run_agent() -> None:
    configure_logging()
    client = create_client()
    project_root = Path(__file__).resolve().parents[2]
    event_logger = EventLogger(
        project_root / ".agent_data" / "events.jsonl"
    )
    history_store = ConversationStore(
        project_root / ".agent_data" / "conversation.json"
    )

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

        messages = keep_last_turns(
            history_store.load(SYSTEM_MESSAGE),
            max_turns=10,
        )
        print("已加载历史消息：", len(messages), "条")

        while True:
            task = input("\n你想问什么？输入‘退出’结束：").strip()
            if task == "退出":
                print("对话结束。")
                break
            if task in {"清空历史", "/reset"}:
                history_store.reset()
                messages = [SYSTEM_MESSAGE]
                print("对话历史已清空。")
                continue
            if not task:
                continue

            messages.append({"role": "user", "content": task})
            messages = keep_last_turns(messages, max_turns=10)
            history_store.save(messages)

            for _ in range(6):
                model_started_at = time.perf_counter()
                response = client.chat.completions.create(
                    model="deepseek-v4-flash",
                    messages=messages,
                    tools=all_tools,
                    tool_choice="auto",
                    extra_body={"thinking": {"type": "disabled"}},
                )

                message = response.choices[0].message
                model_elapsed_ms = (time.perf_counter() - model_started_at) * 1000
                logger.info(
                    "model_request_completed elapsed_ms=%.1f tool_calls=%d",
                    model_elapsed_ms,
                    len(message.tool_calls or []),
                )
                event_logger.record(
                    "model_request_completed",
                    elapsed_ms=round(model_elapsed_ms, 1),
                    tool_calls=len(message.tool_calls or []),
                )
                messages.append(message.model_dump(exclude_none=True))
                history_store.save(messages)

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
                        event_logger,
                    )

                    print("工具执行结果：", result)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(result),
                    })
                    history_store.save(messages)
            else:
                print("已达到最多6轮，本次问题还没有完成。")

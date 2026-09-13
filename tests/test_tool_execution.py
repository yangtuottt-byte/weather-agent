import pytest

import weather_agent.main as main_module
from weather_agent.main import execute_tool


@pytest.mark.asyncio
async def test_execute_tool_returns_unknown_tool_error():
    result = await execute_tool(
        "not_a_tool",
        {},
        None,
        set(),
    )

    assert result == "错误：未知工具 not_a_tool"


@pytest.mark.asyncio
async def test_execute_tool_logs_and_hides_local_tool_failure(
    monkeypatch,
    caplog,
):
    def failing_weather(city):
        raise TimeoutError("weather service timed out")

    monkeypatch.setattr(
        main_module,
        "get_weather",
        failing_weather,
    )

    with caplog.at_level("ERROR"):
        result = await execute_tool(
            "get_weather",
            {"city": "北京"},
            None,
            set(),
        )

    assert result == "工具执行失败，请稍后重试。"
    assert "weather service timed out" in caplog.text

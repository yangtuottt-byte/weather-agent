import json

from weather_agent.observability import (
    EventLogger,
    load_events,
    tool_sequence_for_run,
)


def test_event_logger_writes_json_lines(tmp_path):
    path = tmp_path / "events.jsonl"
    logger = EventLogger(path)

    logger.record(
        "tool_completed",
        tool_name="get_weather",
        elapsed_ms=12.5,
        success=True,
    )

    line = path.read_text(encoding="utf-8").strip()
    event = json.loads(line)

    assert event["event"] == "tool_completed"
    assert event["run_id"] == logger.run_id
    assert event["tool_name"] == "get_weather"
    assert event["success"] is True
    assert "timestamp" in event


def test_event_logger_can_keep_a_given_run_id(tmp_path):
    logger = EventLogger(tmp_path / "events.jsonl", run_id="run-123")

    logger.record("agent_started")

    assert logger.run_id == "run-123"


def test_tool_sequence_is_filtered_by_run_and_success(tmp_path):
    path = tmp_path / "events.jsonl"
    first = EventLogger(path, run_id="run-1")
    second = EventLogger(path, run_id="run-2")

    first.record("tool_completed", tool_name="get_weather", success=True)
    first.record("tool_completed", tool_name="packing_list", success=False)
    second.record("tool_completed", tool_name="get_today", success=True)

    events = load_events(path)

    assert tool_sequence_for_run(events, "run-1") == ["get_weather"]
    assert tool_sequence_for_run(events, "run-2") == ["get_today"]

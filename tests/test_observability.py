import json

from weather_agent.observability import EventLogger


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

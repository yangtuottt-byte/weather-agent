"""Structured runtime events for debugging and later evaluation."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EventLogger:
    """Append one JSON object per runtime event."""

    def __init__(self, path: str | Path, run_id: str | None = None):
        self.path = Path(path)
        self.run_id = run_id or uuid.uuid4().hex

    def record(self, event: str, **fields: Any) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "run_id": self.run_id,
            "event": event,
            **fields,
        }

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_events(path: str | Path) -> list[dict[str, Any]]:
    """Read JSONL events, skipping empty lines."""
    event_path = Path(path)
    if not event_path.exists():
        return []

    events = []
    for line in event_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events


def tool_sequence_for_run(
    events: list[dict[str, Any]],
    run_id: str,
) -> list[str]:
    """Extract successful tool calls for one Agent run."""
    return [
        event["tool_name"]
        for event in events
        if event.get("run_id") == run_id
        and event.get("event") == "tool_completed"
        and event.get("success") is True
    ]

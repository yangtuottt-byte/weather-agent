"""Small JSON-backed conversation history store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConversationStore:
    """Save and load one conversation for the local command-line demo."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self, system_message: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.path.exists():
            return [system_message]

        messages = json.loads(self.path.read_text(encoding="utf-8"))

        if not isinstance(messages, list):
            raise ValueError("对话历史必须是消息列表")

        if not all(isinstance(message, dict) for message in messages):
            raise ValueError("对话历史中的每条消息都必须是对象")

        return messages

    def save(self, messages: list[Any]) -> None:
        serializable_messages = [self._to_dict(message) for message in messages]
        self.path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = self.path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps(
                serializable_messages,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary_path.replace(self.path)

    def reset(self) -> None:
        if self.path.exists():
            self.path.unlink()

    @staticmethod
    def _to_dict(message: Any) -> dict[str, Any]:
        if isinstance(message, dict):
            return message

        if hasattr(message, "model_dump"):
            return message.model_dump(exclude_none=True)

        raise TypeError("消息必须是字典或支持 model_dump 的对象")


def keep_last_turns(
    messages: list[dict[str, Any]],
    max_turns: int,
) -> list[dict[str, Any]]:
    """Keep the system message and complete recent user turns."""
    if max_turns < 1:
        raise ValueError("max_turns 必须至少为 1")

    if not messages:
        return []

    system_messages = [
        message for message in messages
        if message.get("role") == "system"
    ]
    system_message = system_messages[:1]

    turns: list[list[dict[str, Any]]] = []
    current_turn: list[dict[str, Any]] = []

    for message in messages:
        if message.get("role") == "system":
            continue

        if message.get("role") == "user" and current_turn:
            turns.append(current_turn)
            current_turn = []

        current_turn.append(message)

    if current_turn:
        turns.append(current_turn)

    selected_turns = turns[-max_turns:]
    return system_message + [
        message
        for turn in selected_turns
        for message in turn
    ]

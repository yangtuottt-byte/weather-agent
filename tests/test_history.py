import pytest

from weather_agent.history import ConversationStore, keep_last_turns


def test_conversation_store_saves_and_loads_messages(tmp_path):
    path = tmp_path / "conversation.json"
    store = ConversationStore(path)
    messages = [
        {"role": "system", "content": "你是助手。"},
        {"role": "user", "content": "你好"},
    ]

    store.save(messages)

    assert store.load(messages[0]) == messages


def test_conversation_store_can_reset(tmp_path):
    path = tmp_path / "conversation.json"
    store = ConversationStore(path)
    store.save([{"role": "user", "content": "测试"}])

    store.reset()

    assert not path.exists()


def test_keep_last_turns_preserves_complete_recent_turns():
    messages = [
        {"role": "system", "content": "系统"},
        {"role": "user", "content": "问题1"},
        {"role": "assistant", "content": "回答1"},
        {"role": "user", "content": "问题2"},
        {"role": "assistant", "tool_calls": [{"id": "call-2"}]},
        {"role": "tool", "tool_call_id": "call-2", "content": "结果2"},
        {"role": "assistant", "content": "回答2"},
        {"role": "user", "content": "问题3"},
        {"role": "assistant", "content": "回答3"},
    ]

    result = keep_last_turns(messages, max_turns=2)

    assert [message["role"] for message in result] == [
        "system",
        "user",
        "assistant",
        "tool",
        "assistant",
        "user",
        "assistant",
    ]
    assert result[1]["content"] == "问题2"
    assert result[-1]["content"] == "回答3"


def test_keep_last_turns_rejects_invalid_limit():
    with pytest.raises(ValueError):
        keep_last_turns([], max_turns=0)

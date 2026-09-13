from weather_agent.history import ConversationStore


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

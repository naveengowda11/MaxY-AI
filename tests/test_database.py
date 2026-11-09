from memory.database import ChatStore


def test_conversation_and_message_round_trip(tmp_path):
    store = ChatStore(tmp_path / "nested" / "maxy-test.db")
    store.initialize()

    conversation_id = store.create_conversation("Test chat")
    store.add_message(conversation_id, "user", "Hello")
    store.add_message(conversation_id, "assistant", "Hi there")

    assert store.conversation_exists(conversation_id)
    assert store.get_recent_messages(conversation_id) == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
    assert len(store.get_messages(conversation_id)) == 2
    assert store.list_conversations()[0]["title"] == "Test chat"


def test_message_role_is_validated(tmp_path):
    store = ChatStore(tmp_path / "maxy-test.db")
    store.initialize()
    conversation_id = store.create_conversation()

    try:
        store.add_message(conversation_id, "system", "not allowed")
    except ValueError as exc:
        assert "role" in str(exc)
    else:
        raise AssertionError("Invalid message role should be rejected")

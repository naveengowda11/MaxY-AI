from fastapi.testclient import TestClient

from api.server import create_app
from config import Settings
from core.assistant import AssistantService
from memory.database import ChatStore


class FakeLLM:
    async def chat(self, messages):
        assert messages[-1]["role"] == "user"
        return "Hello from the test model."


def build_test_app(database_path):
    settings = Settings(database_path=str(database_path))
    store = ChatStore(database_path)
    assistant = AssistantService(store, FakeLLM())
    return create_app(settings=settings, store=store, assistant=assistant)


def test_health_endpoint(tmp_path):
    app = build_test_app(tmp_path / "maxy.db")
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["app"] == "MAXY"


def test_chat_creates_and_reuses_conversation(tmp_path):
    app = build_test_app(tmp_path / "maxy.db")
    with TestClient(app) as client:
        first = client.post("/api/chat", json={"message": "Hello MAXY"})
        assert first.status_code == 200
        data = first.json()
        assert data["reply"] == "Hello from the test model."

        second = client.post(
            "/api/chat",
            json={
                "message": "Remember this follow-up",
                "conversation_id": data["conversation_id"],
            },
        )
        assert second.status_code == 200

        history = client.get(
            f"/api/conversations/{data['conversation_id']}/messages"
        )

    assert len(history.json()) == 4
    assert history.json()[0]["content"] == "Hello MAXY"


def test_unknown_conversation_returns_404(tmp_path):
    app = build_test_app(tmp_path / "maxy.db")
    with TestClient(app) as client:
        response = client.post(
            "/api/chat",
            json={"message": "Hello", "conversation_id": "missing"},
        )

    assert response.status_code == 404

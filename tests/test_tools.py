from fastapi.testclient import TestClient

from api.server import create_app
from config import Settings
from core.assistant import AssistantService
from memory.database import ChatStore
from tools.registry import ToolError, ToolRegistry


class FakeLLM:
    async def chat(self, messages):
        return "Test reply"


def build_app(tmp_path):
    settings = Settings(database_path=str(tmp_path / "maxy.db"))
    store = ChatStore(settings.database_path)
    assistant = AssistantService(store, FakeLLM())
    app = create_app(settings=settings, store=store, assistant=assistant)
    app.state.tool_registry = ToolRegistry(
        [tmp_path / "workspace"], app_launcher=lambda _app: None
    )
    from tools.approval import ApprovalService
    app.state.approvals = ApprovalService(store, app.state.tool_registry)
    return app


def test_proposal_does_not_execute_until_approved(tmp_path):
    calls = []
    app = build_app(tmp_path)
    app.state.tool_registry.app_launcher = calls.append
    with TestClient(app) as client:
        proposal = client.post(
            "/api/tools/proposals",
            json={"tool_name": "launch_app", "arguments": {"app": "notepad"}},
        )
        assert proposal.status_code == 200
        assert calls == []
        response = client.post(
            f"/api/tools/proposals/{proposal.json()['proposal_id']}/approve",
            json={"approval_phrase": "APPROVE"},
        )
    assert response.status_code == 200
    assert calls == ["notepad"]


def test_approval_is_single_use(tmp_path):
    with TestClient(build_app(tmp_path)) as client:
        proposal = client.post(
            "/api/tools/proposals",
            json={"tool_name": "launch_app", "arguments": {"app": "calculator"}},
        ).json()
        endpoint = f"/api/tools/proposals/{proposal['proposal_id']}/approve"
        assert client.post(endpoint, json={"approval_phrase": "APPROVE"}).status_code == 200
        assert client.post(endpoint, json={"approval_phrase": "APPROVE"}).status_code == 409


def test_invalid_tool_and_app_are_rejected(tmp_path):
    with TestClient(build_app(tmp_path)) as client:
        invalid_tool = client.post(
            "/api/tools/proposals",
            json={"tool_name": "run_shell", "arguments": {"command": "whoami"}},
        )
        invalid_app = client.post(
            "/api/tools/proposals",
            json={"tool_name": "launch_app", "arguments": {"app": "powershell"}},
        )
    assert invalid_tool.status_code == 422
    assert invalid_app.status_code == 422


def test_workspace_path_traversal_is_blocked(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "readme.txt").write_text("local content", encoding="utf-8")
    (tmp_path / "outside.txt").write_text("private", encoding="utf-8")
    registry = ToolRegistry([workspace])
    assert registry.read_text_file({"path": "readme.txt"})["content"] == "local content"
    try:
        registry.read_text_file({"path": "../outside.txt"})
    except ToolError:
        pass
    else:
        raise AssertionError("Workspace traversal should be rejected")


def test_file_extension_and_size_are_restricted(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / "unsafe.exe").write_bytes(b"no")
    registry = ToolRegistry([workspace])
    try:
        registry.preview("read_text_file", {"path": "unsafe.exe"})
    except ToolError:
        pass
    else:
        raise AssertionError("Executable files must not be previewable")


def test_chat_command_creates_proposal_without_executing(tmp_path):
    calls = []
    app = build_app(tmp_path)
    app.state.tool_registry.app_launcher = calls.append
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Maxy, open Calculator"})
    assert response.status_code == 200
    data = response.json()
    assert data["pending_action"]["tool_name"] == "launch_app"
    assert data["pending_action"]["arguments"] == {"app": "calculator"}
    assert data["pending_action"]["preview"]["target"] == "calculator"
    assert calls == []


def test_chat_search_intent_creates_workspace_proposal(tmp_path):
    with TestClient(build_app(tmp_path)) as client:
        response = client.post(
            "/api/chat", json={"message": "find my file named internship"}
        )
    assert response.status_code == 200
    action = response.json()["pending_action"]
    assert action["tool_name"] == "search_files"
    assert action["arguments"] == {"query": "internship"}


def test_explicit_memory_and_task_commands_work_without_llm(tmp_path):
    app = build_app(tmp_path)
    with TestClient(app) as client:
        remembered = client.post("/api/chat", json={"message": "remember that I like Java"})
        assert "Saved to your local memory" in remembered.json()["reply"]

        recall = client.post("/api/chat", json={"message": "what do you remember about me"})
        assert "I like Java" in recall.json()["reply"]

        added = client.post("/api/chat", json={"message": "remind me to finish MaxY stage"})
        assert "Added task" in added.json()["reply"]

        tasks = client.post("/api/chat", json={"message": "show my tasks"})
        assert "finish MaxY stage" in tasks.json()["reply"]

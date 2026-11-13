import os
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.server import create_app
from config import Settings
from core.assistant import AssistantService
from memory.database import ChatStore


class FakeLLM:
    async def chat(self, messages):
        return "Test reply"


class FakeVoice:
    def transcribe(self, audio_bytes, suffix=".webm"):
        assert audio_bytes == b"fake-audio"
        return "Turn on the lights"

    def synthesize(self, text):
        descriptor, filename = tempfile.mkstemp(suffix=".wav")
        os.close(descriptor)
        path = Path(filename)
        path.write_bytes(b"RIFF" + b"0" * 48)
        return path


def build_app(tmp_path, voice_enabled=True):
    settings = Settings(
        database_path=str(tmp_path / "maxy.db"),
        voice_enabled=voice_enabled,
    )
    store = ChatStore(settings.database_path)
    assistant = AssistantService(store, FakeLLM())
    app = create_app(settings=settings, store=store, assistant=assistant)
    app.state.voice = FakeVoice()
    return app


def test_voice_status_is_reported(tmp_path):
    with TestClient(build_app(tmp_path)) as client:
        response = client.get("/api/voice/status")

    assert response.status_code == 200
    assert response.json()["enabled"] is True


def test_voice_transcription_endpoint(tmp_path):
    with TestClient(build_app(tmp_path)) as client:
        response = client.post(
            "/api/voice/transcribe",
            files={"audio": ("recording.webm", b"fake-audio", "audio/webm")},
        )

    assert response.status_code == 200
    assert response.json()["text"] == "Turn on the lights"


def test_voice_disabled_by_default(tmp_path):
    with TestClient(build_app(tmp_path, voice_enabled=False)) as client:
        response = client.post(
            "/api/voice/transcribe",
            files={"audio": ("recording.webm", b"fake-audio", "audio/webm")},
        )

    assert response.status_code == 503


def test_speak_endpoint_returns_audio_file(tmp_path):
    with TestClient(build_app(tmp_path)) as client:
        response = client.post(
            "/api/voice/speak",
            json={"text": "Hello from MAXY"},
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/wav")
    assert response.content.startswith(b"RIFF")

"""FastAPI application factory for MAXY."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routes import router
from config import Settings, get_settings
from core.assistant import AssistantService
from core.llm import OllamaClient
from memory.database import ChatStore
from voice.routes import router as voice_router
from voice.service import VoiceService

INTERFACE_DIR = Path(__file__).resolve().parent.parent / "interface"


def create_app(
    settings: Settings | None = None,
    store: ChatStore | None = None,
    assistant: AssistantService | None = None,
    voice_service: VoiceService | None = None,
) -> FastAPI:
    app_settings = settings or get_settings()
    chat_store = store or ChatStore(app_settings.database_path)
    llm_client = OllamaClient(
        base_url=app_settings.ollama_base_url,
        model=app_settings.ollama_model,
        timeout_seconds=app_settings.request_timeout_seconds,
    )
    assistant_service = assistant or AssistantService(
        store=chat_store,
        llm=llm_client,
        max_history_messages=app_settings.max_history_messages,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        chat_store.initialize()
        yield

    app = FastAPI(
        title="MAXY AI",
        description="Local-first personal AI assistant",
        version="0.3.0",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.store = chat_store
    app.state.assistant = assistant_service
    app.state.voice = voice_service or VoiceService(app_settings)
    app.include_router(router)
    app.include_router(voice_router)

    if INTERFACE_DIR.exists():
        app.mount(
            "/static",
            StaticFiles(directory=str(INTERFACE_DIR)),
            name="static",
        )

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(INTERFACE_DIR / "index.html")

    return app


app = create_app()

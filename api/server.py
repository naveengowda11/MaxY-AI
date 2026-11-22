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
from tools.approval import ApprovalService
from tools.registry import ToolRegistry
from tools.routes import router as tools_router
from voice.routes import router as voice_router
from voice.service import VoiceService

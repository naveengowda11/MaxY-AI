"""Local voice endpoints. Audio is processed on this machine."""
import asyncio
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from voice.service import VoiceError

"""Local voice endpoints. Audio is processed on this machine."""
import asyncio
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from core.llm import LLMError
from voice.service import VoiceError

router = APIRouter(prefix="/api/voice", tags=["voice"])
MAX_AUDIO_BYTES = 20 * 1024 * 1024


def _remove_file(path: Path) -> None:
    path.unlink(missing_ok=True)


def _require_voice(request: Request) -> None:
    if not request.app.state.settings.voice_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voice is disabled. Set MAXY_VOICE_ENABLED=true in your .env file.",
        )


@router.get("/status")
async def voice_status(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return {
        "enabled": settings.voice_enabled,
        "wake_word_enabled": settings.wake_word_enabled,
        "speech_to_text": "faster-whisper (CPU, local)",
        "text_to_speech": "Windows SAPI via pyttsx3 (local)",
        "stt_model": settings.voice_stt_model,
    }


@router.post("/transcribe")
async def transcribe(
    request: Request,
    audio: UploadFile = File(...),
) -> dict[str, str]:
    _require_voice(request)
    content_type = (audio.content_type or "").lower()
    if not (
        content_type.startswith("audio/")
        or content_type in {"video/webm", "application/octet-stream"}
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Upload a supported audio recording.",
        )

    audio_bytes = await audio.read(MAX_AUDIO_BYTES + 1)
    await audio.close()
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Recording is too large. Keep it under 20 MB.",
        )

    suffix = Path(audio.filename or "recording.webm").suffix.lower()
    try:
        transcript = await asyncio.to_thread(
            request.app.state.voice.transcribe, audio_bytes, suffix
        )
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return {"text": transcript}


@router.post("/speak")
async def speak(request: Request, payload: dict[str, str]) -> FileResponse:
    _require_voice(request)
    text = payload.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=422, detail="Text is required.")
    try:
        audio_path = await asyncio.to_thread(request.app.state.voice.synthesize, text)
    except VoiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename="maxy-response.wav",
        background=BackgroundTask(_remove_file, audio_path),
    )

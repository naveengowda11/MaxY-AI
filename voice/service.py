"""Optional offline speech recognition and speech synthesis adapters."""
import tempfile
import wave
from pathlib import Path

from config import Settings


class VoiceError(RuntimeError):
    """Raised when a local voice operation cannot be completed."""


class VoiceService:
    """Lazy-loads local speech models so text-only MAXY stays lightweight."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._stt_model = None

    def transcribe(self, audio_bytes: bytes, suffix: str = ".webm") -> str:
        if not audio_bytes:
            raise VoiceError("The recording was empty.")

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise VoiceError(
                "Voice dependencies are missing. Install the optional voice requirements."
            ) from exc

        if self._stt_model is None:
            try:
                self._stt_model = WhisperModel(
                    self.settings.voice_stt_model,
                    device="cpu",
                    compute_type="int8",
                )
            except Exception as exc:
                raise VoiceError(
                    "Could not load the speech model. Check the model name and internet "
                    "connection for its first download."
                ) from exc

        safe_suffix = suffix if suffix in {".webm", ".wav", ".ogg", ".mp4", ".m4a"} else ".webm"
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=safe_suffix, delete=False) as audio_file:
                audio_file.write(audio_bytes)
                temp_path = Path(audio_file.name)

            segments, _info = self._stt_model.transcribe(
                str(temp_path),
                beam_size=1,
                vad_filter=True,
            )
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
        except Exception as exc:
            raise VoiceError(
                "Could not transcribe the recording. Try recording again with a clear voice."
            ) from exc
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)

        if not transcript:
            raise VoiceError("I couldn't hear any speech. Please try again.")
        return transcript

    def synthesize(self, text: str) -> Path:
        clean_text = text.strip()
        if not clean_text:
            raise VoiceError("There is no text to speak.")
        if len(clean_text) > 5000:
            raise VoiceError("The text is too long to read aloud (maximum 5,000 characters).")

        try:
            import pyttsx3
        except ImportError as exc:
            raise VoiceError(
                "Offline speech output is unavailable. Install the optional voice requirements."
            ) from exc

        output_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as output_file:
                output_path = Path(output_file.name)

            engine = pyttsx3.init()
            engine.setProperty("rate", self.settings.voice_tts_rate)
            engine.setProperty("volume", self.settings.voice_tts_volume)
            engine.save_to_file(clean_text, str(output_path))
            engine.runAndWait()
            engine.stop()

            if not output_path.exists() or output_path.stat().st_size < 44:
                raise RuntimeError("The speech engine did not create a valid audio file.")
            return output_path
        except Exception as exc:
            if output_path is not None:
                output_path.unlink(missing_ok=True)
            raise VoiceError(
                "Windows could not generate speech. Check that a Windows speech voice is installed."
            ) from exc

# Voice

Stage 3 provides optional, local voice interaction:
- Browser push-to-talk microphone capture.
- faster-whisper speech-to-text, loaded lazily on CPU.
- pyttsx3 speech synthesis using installed Windows SAPI voices.
- Audio is posted only to the local MAXY API; temporary transcription files are deleted.
- Voice dependencies are optional; text-only operation remains available.

Install `requirements-voice.txt` and set `MAXY_VOICE_ENABLED=true` in `.env`. The first faster-whisper model download needs internet access; subsequent inference is local. The current Windows SAPI voice is an offline baseline, not a neural-quality voice clone.

Wake-word detection and always-listening microphone capture are intentionally not included.

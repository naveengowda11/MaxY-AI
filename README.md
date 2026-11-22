# MAXY AI

**MAXY — Your Personal Intelligence System**

A local-first personal AI assistant for Windows, designed to grow into a Windows + Android companion. MAXY combines a local language model, conversation memory, optional voice interaction, and a permission-first tool architecture.

## Current release: Stage 3 — Push-to-talk voice (initial implementation)

The repository includes:
- FastAPI application and health endpoint.
- Local Ollama chat integration.
- SQLite conversation and message persistence.
- Responsive browser-based chat interface.
- Optional local speech-to-text using faster-whisper on CPU.
- Optional offline text-to-speech using installed Windows SAPI voices through pyttsx3.
- Browser push-to-talk recording and voice playback controls.
- Unit and API tests for core and voice endpoints.

Voice is opt-in and text mode remains available. Stage 4 adds a safe-action panel for fixed app launching and workspace-only file tools, with one-time approval.

## Quick start (Windows)

Requirements: Python 3.11+, Git, and Ollama.

```powershell
git clone https://github.com/naveengowda11/MaxY-AI.git
cd MaxY-AI
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-voice.txt
Copy-Item .env.example .env
```

Edit `.env` and set `MAXY_VOICE_ENABLED=true`. Keep `MAXY_WAKE_WORD_ENABLED=false`; always-listening wake-word detection is not part of this release.

Start the local model and app:

```powershell
ollama pull llama3.2:1b
python main.py
```

Open http://127.0.0.1:8765. Allow microphone access when your browser asks. Use the microphone button to start recording, then press it again to stop and send the transcript to MAXY.

The first speech-recognition model download requires an internet connection. After the model is cached locally, transcription runs locally. Speech playback uses the Windows voices installed on your computer; voice quality varies by installed voice.

## Run tests

```powershell
pytest -q
ruff check .
```

## Architecture and safety
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Setup and troubleshooting](docs/SETUP.md)
- [Security baseline](docs/SECURITY.md)

The API binds to localhost by default. Do not expose it to the LAN or public internet. Authenticated Android pairing is not implemented yet. Audio recordings are processed in temporary files and deleted after transcription. Stage 4 file tools are confined to the MAXY project workspace.

## License
MIT. See [LICENSE](LICENSE).

## Personal memory and tasks

Stage 5 adds explicit, local memory and a basic task list:

- Say `remember that I prefer concise explanations` to save a memory.
- Ask `what do you remember about me` to list saved facts (each item shows an ID).
- Say `forget memory <ID>` to remove a saved fact.
- Say `remind me to prepare the demo` or `add task Prepare demo` to create a task.
- Say `show my tasks` to list open tasks.
- Say `complete task <8-character-ID>` to mark a task complete.

Open **Memory & tasks** in the sidebar to view, add, and delete memories or tasks.

This release stores tasks locally but does not yet schedule operating-system notifications, sync a calendar, or deliver phone push reminders. Those integrations require a later stage.

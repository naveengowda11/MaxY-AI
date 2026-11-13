# Development Setup

## Prerequisites
- Windows 10/11 (64-bit)
- Python 3.11+
- Git
- Ollama for local inference
- A microphone and speakers/headphones for voice use

Install Ollama from https://ollama.com/download.

## Clone and install
```powershell
git clone https://github.com/naveengowda11/MaxY-AI.git
cd MaxY-AI
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-voice.txt
```

## Start the local model
```powershell
ollama pull llama3.2:1b
ollama list
```

Keep Ollama running in the background. Chat inference runs locally.

## Configure voice
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

Open `.env` and set:
```dotenv
MAXY_VOICE_ENABLED=true
MAXY_WAKE_WORD_ENABLED=false
MAXY_VOICE_STT_MODEL=base
MAXY_VOICE_TTS_RATE=180
MAXY_VOICE_TTS_VOLUME=1.0
```

Voice is disabled by default. Install `requirements-voice.txt` before enabling it. The first use of faster-whisper downloads the selected model and therefore needs internet access; later transcription can run offline. The default `base` model is a compromise between accuracy, speed, and memory. If your laptop is slow, change it to `tiny`; for better accuracy with more CPU/RAM use `small`.

Speech output uses pyttsx3 with installed Windows SAPI voices. The sound is offline and functional, but naturalness depends on the Windows voice installed. A neural offline voice engine can be evaluated in a later iteration.

## Run MAXY
```powershell
python main.py
```

Open http://127.0.0.1:8765. The browser microphone API works on localhost in modern browsers. Click the microphone button once to start recording, speak, then click again to stop. MAXY transcribes locally, sends the text to Ollama, and plays the answer using the local Windows voice.

API health: http://127.0.0.1:8765/api/health
Voice status: http://127.0.0.1:8765/api/voice/status

## Run tests
```powershell
pytest -q
ruff check .
```

## Troubleshooting
- **Ollama connection error:** open the Ollama app, then run `ollama list`.
- **Model missing:** run `ollama pull llama3.2:1b`.
- **Voice disabled:** check `MAXY_VOICE_ENABLED=true` in `.env` and restart MAXY.
- **Voice dependency missing:** activate the virtual environment and run `pip install -r requirements-voice.txt`.
- **First transcription is slow:** faster-whisper downloads and loads its model on first use.
- **No speech detected:** speak close to the microphone in a quiet room.
- **Speech playback fails:** verify that Windows has a working SAPI speech voice installed.
- **Microphone unavailable:** allow microphone permission for localhost in your browser and check Windows microphone privacy settings.
- **Port already in use:** set a different `MAXY_PORT` in `.env`.

Wake-word detection, always-listening capture, computer control, and Android pairing are not part of this stage.

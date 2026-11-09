# MAXY AI

**MAXY — Your Personal Intelligence System**

A local-first personal AI assistant for Windows, designed to grow into a Windows + Android companion. MAXY is built around voice interaction, a local language model, persistent memory, computer tools, and explicit user approval for consequential actions.

## Current release: Stage 2 — Text assistant

The repository now includes:
- FastAPI application and health endpoint.
- Local Ollama chat integration (no paid cloud inference API).
- SQLite conversation and message persistence.
- Conversation history restoration in the web interface.
- Responsive browser-based chat UI.
- Unit and API tests.

Voice, wake-word detection, computer control, and Android device pairing are future milestones, not current capabilities.

## Quick start (Windows)

Requirements: Python 3.11+, Git, and Ollama.

```powershell
git clone https://github.com/naveengowda11/MaxY-AI.git
cd MaxY-AI
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull llama3.2:1b
python main.py
```

Open http://127.0.0.1:8765.

Keep Ollama running. The first model response may take longer while the model loads.

## Run tests

```powershell
pytest -q
```

## Architecture and safety
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Setup and troubleshooting](docs/SETUP.md)
- [Security baseline](docs/SECURITY.md)

The API binds to localhost by default. Do not expose it to the LAN or public internet. Authenticated Android pairing is not implemented yet.

## License
MIT. See [LICENSE](LICENSE).

# Development Setup

## Prerequisites
- Windows 10/11 (64-bit)
- Python 3.11+
- Git
- Ollama for local inference

Install Ollama from https://ollama.com/download.

## Clone and create a virtual environment
```powershell
git clone https://github.com/naveengowda11/MaxY-AI.git
cd MaxY-AI
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Start the local model
```powershell
ollama pull llama3.2:1b
ollama list
```

Keep Ollama running in the background. The model runs locally; MAXY does not use a paid cloud inference API.

## Configure MAXY
Copy the example environment file:
```powershell
Copy-Item .env.example .env
```

The default API address is `127.0.0.1:8765`. This is intentionally localhost-only. Do not change the host to `0.0.0.0` or expose the port to your network; authenticated Android pairing is a later milestone.

## Run MAXY
```powershell
python main.py
```

Open http://127.0.0.1:8765 in your browser. API health is available at http://127.0.0.1:8765/api/health.

## Run tests
```powershell
pytest -q
```

## Troubleshooting
- **Ollama connection error:** open the Ollama app, then run `ollama list`.
- **Model missing:** run `ollama pull llama3.2:1b`.
- **Port already in use:** set a different `MAXY_PORT` in `.env`.
- **PowerShell activation blocked:** run `.venv\Scripts\python.exe -m pip install -r requirements.txt` and use that interpreter directly.

The initial release is text-only. Voice, wake-word detection, computer control, and Android pairing are not included yet.

# Development Setup

This initial commit is a structural foundation, not a runnable assistant. Setup commands for the application will be finalized with the first executable milestone.

## Prerequisites
- Windows 10/11 (64-bit)
- Python 3.11+
- Git
- Ollama for local inference

Ollama: https://ollama.com/download

## Clone
```powershell
git clone https://github.com/naveengowda11/MaxY-AI.git
cd MaxY-AI
```

## Virtual environment
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by PowerShell policy, use `.venv\Scripts\python.exe` directly or adjust the policy according to your organization's guidance.

## Verify local model runtime
```powershell
ollama --version
ollama list
```

The selected model will be based on measured response quality and RAM use on the target laptop.

## Android
The first Android client will be a responsive web interface served by the Windows host. LAN pairing and authentication must exist before network access is enabled. Do not expose an unauthenticated development server to the public internet.

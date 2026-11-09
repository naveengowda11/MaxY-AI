# MAXY AI

**MAXY — Your Personal Intelligence System**

A local-first personal AI assistant for Windows, designed to grow into a Windows + Android companion. MAXY is planned around voice interaction, a local language model, persistent memory, computer tools, and explicit user approval for consequential actions.

> Status: **Stage 1 — architecture and repository foundation.** Runtime features are not implemented yet.

## Principles
- Local-first: basic conversations use a local model without a cloud API.
- Permission before action: consequential actions require clear, scoped user approval.
- Modular: voice, reasoning, memory, tools, API, and interface stay separate.
- Honest status: unimplemented features are never presented as working.
- Secure cross-device access: Android pairing must be authenticated; no public unauthenticated server.

## Planned architecture
```text
Windows desktop / Android companion
              |
         FastAPI gateway
              |
        MAXY assistant core
       /         |          \
  Local LLM    Memory    Permission gate
       |         |          |
    Ollama     SQLite    Tool registry
                           |
                   Windows / browser tools

Voice -> Wake word -> Speech-to-text -> Core -> Text-to-speech
```

## Technology direction
| Area | Initial choice |
|---|---|
| Runtime | Python 3.11+ |
| Local inference | Ollama |
| API | FastAPI + Uvicorn |
| Speech recognition | faster-whisper (optional) |
| Wake word | openWakeWord (optional) |
| Speech synthesis | Kokoro (optional; separate model setup) |
| Storage | SQLite |
| Desktop automation | PyAutoGUI, behind approval gates |
| Browser automation | Playwright, behind approval gates |
| UI | HTML, CSS, vanilla JavaScript |
| Android | Responsive web companion first |

Hardware target is an 8 GB Windows laptop. Model and audio workloads will be staged to control RAM use.

## Repository guide
- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Setup](docs/SETUP.md)
- [Security](docs/SECURITY.md)

## Current state
This initial commit establishes structure, boundaries, documentation, and configuration only. The assistant is not runnable yet.

- [x] Architecture and module boundaries
- [x] Configuration template and development guidance
- [ ] Local LLM conversation runtime
- [ ] Voice input/output and wake word
- [ ] SQLite conversation memory
- [ ] Approval workflow and restricted tools
- [ ] Windows dashboard
- [ ] Authenticated Android companion
- [ ] Automated tests and packaging

## Configuration
Copy `.env.example` to `.env`. Never commit real credentials, tokens, or device secrets.

## License
This repository includes the MIT License. See [LICENSE](LICENSE) for the terms.

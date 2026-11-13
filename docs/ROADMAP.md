# MAXY Roadmap

## Stage 1 — Foundation
- [x] Repository layout
- [x] Architecture and security baseline
- [x] Environment template and development guidance

## Stage 2 — Text assistant
- [x] FastAPI application and health endpoint
- [x] Ollama local chat adapter
- [x] Conversation endpoint and SQLite history
- [x] Responsive web chat interface
- [x] Unit and API tests
- [ ] Verify on target Windows laptop with local Ollama

## Stage 3 — Voice
- [x] Optional local speech-to-text adapter (faster-whisper)
- [x] Offline speech output using Windows SAPI voices
- [x] Browser microphone capture and push-to-talk controls
- [x] Voice transcript to assistant conversation pipeline
- [x] Voice endpoint tests and audio upload size limits
- [ ] Verify microphone and speaker devices on target Windows laptop
- [ ] Evaluate a neural offline TTS voice for more natural speech
- [ ] Opt-in wake-word detection (separate, later milestone)

## Stage 4 — Safe actions
- [ ] Typed tool registry and approval lifecycle
- [ ] Restricted application launcher
- [ ] Safe file listing/search
- [ ] Browser automation with approval
- [ ] Audit log

## Stage 5 — Memory and daily planning
- [ ] User-approved long-term memory
- [ ] Reminders and tasks
- [ ] Calendar integration
- [ ] Email integration with drafts-first behavior

## Stage 6 — Android companion
- [ ] Device pairing
- [ ] Authenticated local-network API
- [ ] Mobile interface
- [ ] Secure token storage and revocation
- [ ] Remote access only after security review

## Stage 7 — Packaging
- [ ] Windows startup/tray behavior
- [ ] Installer
- [ ] Diagnostics
- [ ] Backup/export and deletion controls

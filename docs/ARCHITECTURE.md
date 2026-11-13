# MAXY Architecture

## Goals
MAXY is a personal assistant hosted primarily on Windows. The Windows service owns model execution, tools, memory, and policy decisions. Android is a companion client.

## Layers

### Clients
- Windows browser-based dashboard initially.
- Responsive Android web companion initially.
- Clients send requests to the API; they do not execute privileged tools.

### API
- FastAPI provides health, conversation, and later device-pairing endpoints.
- Localhost binding is the default.
- LAN access requires explicit opt-in and authentication.

### Assistant core
- Receives user input and bounded conversation context.
- Calls a configured local model through a provider adapter.
- Returns an answer or a structured tool proposal.
- Never executes model-generated code.

### Policy and tools
- Tool requests use typed schemas and an allowlist.
- Side-effecting actions are presented for approval.
- Arguments are revalidated immediately before execution.
- Results and audit metadata are recorded.

### Memory
- SQLite stores conversation history and user-approved memories.
- Sensitive information is not automatically promoted into long-term memory.
- Future releases must support inspection, correction, export, and deletion.

### Voice
- Browser push-to-talk capture sends audio to the localhost API.
- faster-whisper performs local CPU speech-to-text after its model is cached.
- pyttsx3 uses installed Windows SAPI voices for offline speech output.
- Voice remains opt-in; text interaction works independently.
- Wake-word detection and always-listening capture are not enabled in the current release.
- Temporary audio files are deleted after processing; audio/model/device failures are surfaced.

## Request lifecycle
1. Client submits text or transcription.
2. API validates the request and loads conversation context.
3. Core calls the local model.
4. Normal answers return to the client.
5. Tool proposals are validated and displayed for approval.
6. Approved actions are revalidated and executed by a restricted handler.
7. Results and audit metadata are stored; the assistant reports the outcome.

## Reliability
- Typed request/response models.
- Bounded timeouts.
- No silent cloud fallback.
- Clear diagnostics when local services are unavailable.
- Tests for permission decisions and tool input validation.

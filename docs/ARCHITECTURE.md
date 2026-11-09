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
- Wake-word detection, capture, speech-to-text, and text-to-speech are separate services.
- Voice remains optional; text interaction must work independently.
- Audio/model/device failures must be visible.

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

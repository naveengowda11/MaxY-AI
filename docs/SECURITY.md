# Security and Privacy Baseline

MAXY may eventually control files, applications, and connected accounts. These rules are mandatory.

## Permission model
- Read-only capabilities are individually configurable.
- Every external side effect creates a user-visible approval request.
- Approval applies to one action and its exact arguments.
- Changes to target or arguments invalidate prior approval.
- High-impact actions require fresh confirmation immediately before execution.

## Forbidden patterns
- Never execute arbitrary LLM-generated Python, PowerShell, shell, or JavaScript.
- Never permit unrestricted model-selected filesystem paths.
- Never store passwords, cookies, or API tokens in prompts or logs.
- Never silently upload private documents or audio to cloud services.
- Never treat LAN presence as proof that a device is trusted.

## Android connectivity
- Localhost is the default bind address.
- LAN mode requires explicit configuration and authentication.
- Pairing tokens must be high entropy, revocable, and securely stored.
- Use TLS for remote or untrusted networks.
- No router port-forwarding or public tunnel by default.

## Data controls
Future releases must provide memory inspection, correction, export, and deletion. Conversation history and long-term memory must remain distinguishable.

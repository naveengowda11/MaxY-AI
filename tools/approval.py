"""One-shot approval and audit lifecycle for local tool execution."""
import json
import secrets
from datetime import UTC, datetime, timedelta

from memory.database import ChatStore
from tools.registry import ToolError, ToolRegistry

APPROVAL_SECONDS = 90


class ApprovalService:
    def __init__(self, store: ChatStore, registry: ToolRegistry) -> None:
        self.store = store
        self.registry = registry

    def propose(self, tool_name: str, arguments: dict) -> dict:
        preview = self.registry.preview(tool_name, arguments)
        proposal_id = secrets.token_urlsafe(24)
        expiry = (datetime.now(UTC) + timedelta(seconds=APPROVAL_SECONDS)).isoformat()
        self.store.create_tool_proposal(
            proposal_id, tool_name, json.dumps(arguments, sort_keys=True), expiry
        )
        self.store.add_audit_event("proposal_created", tool_name, proposal_id, "pending")
        return {"proposal_id": proposal_id, "tool_name": tool_name, "arguments": arguments,
                "preview": preview, "expires_at": expiry, "approval_phrase": "APPROVE",
                "message": "Review this exact action. Approval expires in 90 seconds and is single-use."}

    def approve_and_execute(self, proposal_id: str, phrase: str) -> dict:
        if phrase != "APPROVE":
            raise ToolError("Approval phrase did not match.")
        proposal = self.store.get_tool_proposal(proposal_id)
        if proposal is None:
            raise ToolError("Approval request was not found or was already used.")
        if datetime.fromisoformat(proposal["expires_at"]) <= datetime.now(timezone.utc):
            self.store.update_tool_proposal(proposal_id, "expired", expected_status="pending")
            self.store.add_audit_event("approval_expired", proposal["tool_name"], proposal_id, "expired")
            raise ToolError("Approval expired. Create a new proposal.")
        if not self.store.update_tool_proposal(proposal_id, "executing", expected_status="pending"):
            raise ToolError("This approval has already been used or is executing.")
        try:
            args = json.loads(proposal["arguments_json"])
            result = self.registry.get(proposal["tool_name"])(args)
        except ToolError as exc:
            self.store.update_tool_proposal(proposal_id, "failed")
            self.store.add_audit_event("tool_failed", proposal["tool_name"], proposal_id, str(exc))
            raise
        except Exception as exc:
            self.store.update_tool_proposal(proposal_id, "failed")
            self.store.add_audit_event("tool_failed", proposal["tool_name"], proposal_id, "Unexpected tool error")
            raise ToolError("Tool failed safely. Check MAXY's local logs.") from exc
        self.store.update_tool_proposal(proposal_id, "completed")
        self.store.add_audit_event("tool_completed", proposal["tool_name"], proposal_id, "success")
        return {"proposal_id": proposal_id, "status": "completed", "result": result}

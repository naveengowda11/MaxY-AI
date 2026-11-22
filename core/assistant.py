"""Conversation orchestration for MAXY."""
from collections.abc import Sequence
from typing import Any

from core.llm import OllamaClient
from memory.database import ChatStore
from tools.approval import ApprovalService
from tools.intent import ToolIntentParser
from tools.registry import ToolError

SYSTEM_PROMPT = (
    "You are MAXY, a helpful personal AI assistant. Be clear, practical, and honest. "
    "You can propose a small set of safe local actions through the approved tool system. "
    "Never claim an action was completed unless the tool reports success. "
    "Do not invent tool access or execute arbitrary commands. Ask clarifying questions "
    "when needed. Keep responses concise unless the user requests detail."
)


class AssistantService:
    def __init__(
        self,
        store: ChatStore,
        llm: OllamaClient,
        max_history_messages: int = 12,
    ) -> None:
        self.store = store
        self.llm = llm
        self.max_history_messages = max_history_messages
        self.intent_parser = ToolIntentParser()

    def create_conversation(self, first_message: str) -> str:
        title = " ".join(first_message.split())[:60] or "New conversation"
        return self.store.create_conversation(title)

    async def reply(self, conversation_id: str, user_message: str) -> str:
        answer, _ = await self.reply_with_action(conversation_id, user_message, None)
        return answer

    async def reply_with_action(
        self,
        conversation_id: str,
        user_message: str,
        approvals: ApprovalService | None,
    ) -> tuple[str, dict[str, Any] | None]:
        self.store.add_message(conversation_id, "user", user_message)
        intent = self.intent_parser.parse(user_message) if approvals else None

        if intent:
            tool_name, arguments = intent
            try:
                proposal = approvals.propose(tool_name, arguments)
            except ToolError as exc:
                reply = f"I couldn't prepare that action: {exc}"
                self.store.add_message(conversation_id, "assistant", reply)
                return reply, None
            reply = (
                f"I prepared a preview for {proposal['preview']['action'].lower()}. "
                "Nothing has run. Review the action card and type APPROVE to execute "
                "this one-time request."
            )
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, proposal

        history: Sequence[dict[str, str]] = self.store.get_recent_messages(
            conversation_id, self.max_history_messages
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
        answer = await self.llm.chat(messages)
        self.store.add_message(conversation_id, "assistant", answer)
        return answer, None

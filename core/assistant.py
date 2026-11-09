"""Conversation orchestration for MAXY."""
from collections.abc import Sequence

from core.llm import OllamaClient
from memory.database import ChatStore

SYSTEM_PROMPT = (
    "You are MAXY, a helpful personal AI assistant. Be clear, practical, and honest. "
    "You are currently in the text-assistant milestone. You cannot control the computer, "
    "send messages, browse privately, or perform background actions yet. Never claim that "
    "you completed an action unless a connected tool actually did it. Ask clarifying "
    "questions when needed. Keep responses concise unless the user requests detail."
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

    def create_conversation(self, first_message: str) -> str:
        title = " ".join(first_message.split())[:60] or "New conversation"
        return self.store.create_conversation(title)

    async def reply(self, conversation_id: str, user_message: str) -> str:
        self.store.add_message(conversation_id, "user", user_message)
        history: Sequence[dict[str, str]] = self.store.get_recent_messages(
            conversation_id, self.max_history_messages
        )
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, *history]
        answer = await self.llm.chat(messages)
        self.store.add_message(conversation_id, "assistant", answer)
        return answer

"""Conversation orchestration for MAXY."""
import re
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
        normalized = " ".join(user_message.strip().split())
        memory_match = re.fullmatch(
            r"(?:maxy[, ]+)?(?:please )?remember(?: that| this)?[: ]+(.+)",
            normalized, flags=re.IGNORECASE,
        )
        if memory_match:
            fact = memory_match.group(1).strip().strip('"').strip("'")
            try:
                saved = self.store.save_memory(fact)
                reply = f"Saved to your local memory: {saved['content']}"
            except ValueError as exc:
                reply = f"I couldn't save that memory: {exc}"
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, None

        if re.search(r"what do you remember about me|show my memories|list my memories", normalized, re.I):
            memories = self.store.list_memories(limit=30)
            if memories:
                reply = "Your saved facts:\\n" + "\\n".join(
                    f"- [{item['id'][:8]}] {item['content']}" for item in memories
                )
            else:
                reply = "You have no saved memories yet. Say 'remember that ...' to save one."
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, None

        forget_match = re.fullmatch(
            r"(?:maxy[, ]+)?(?:please )?(?:forget|delete) memory ([a-f0-9-]{8,36})",
            normalized, re.I,
        )
        if forget_match:
            deleted = self.store.delete_memory(forget_match.group(1))
            reply = "Deleted that local memory." if deleted else "I couldn't find that memory ID."
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, None

        task_match = re.fullmatch(
            r"(?:maxy[, ]+)?(?:please )?(?:add task|remind me to|remember to)[: ]+(.+)",
            normalized, re.I,
        )
        if task_match:
            try:
                task = self.store.create_task(task_match.group(1).strip().strip('"').strip("'"))
                reply = f"Added task [{task['id']}]: {task['title']}"
            except ValueError as exc:
                reply = f"I couldn't add that task: {exc}"
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, None

        if re.search(r"(show|list) (my )?(open )?tasks|what are my tasks", normalized, re.I):
            tasks = self.store.list_tasks(include_completed=False, limit=30)
            reply = ("Open tasks:\\n" + "\\n".join(
                f"- [{task['id']}] {task['title']}" for task in tasks
            )) if tasks else "You have no open tasks."
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, None

        done_match = re.fullmatch(
            r"(?:maxy[, ]+)?(?:please )?(?:complete|finish|mark done) task ([a-f0-9]{8})",
            normalized, re.I,
        )
        if done_match:
            updated = self.store.set_task_status(done_match.group(1), "completed")
            reply = "Marked that task complete." if updated else "I couldn't find that task ID."
            self.store.add_message(conversation_id, "assistant", reply)
            return reply, None

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
        memories = self.store.list_memories(limit=20)
        memory_context = ""
        if memories:
            memory_context = "\\n\\nUser-approved local memory; use only when relevant:\\n"
            memory_context += "\\n".join(f"- {item['content']}" for item in memories)
        messages = [{"role": "system", "content": SYSTEM_PROMPT + memory_context}, *history]
        answer = await self.llm.chat(messages)
        self.store.add_message(conversation_id, "assistant", answer)
        return answer, None

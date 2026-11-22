"""Validated API request and response models."""
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    conversation_id: str | None = Field(default=None, max_length=64)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message cannot be blank.")
        return cleaned


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    pending_action: dict | None = None


class MessageItem(BaseModel):
    role: str
    content: str
    created_at: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class HealthResponse(BaseModel):
    status: str
    app: str
    model: str


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    category: str = Field(default="general", max_length=40)

    @field_validator("content")
    @classmethod
    def memory_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Memory cannot be blank.")
        return value.strip()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    due_at: str | None = Field(default=None, max_length=80)

    @field_validator("title")
    @classmethod
    def task_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Task cannot be blank.")
        return value.strip()


class TaskStatusUpdate(BaseModel):
    status: str = Field(pattern="^(open|completed)$")

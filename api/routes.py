"""HTTP routes for the MAXY text assistant."""
from fastapi import APIRouter, HTTPException, Request, status

from api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationSummary,
    HealthResponse,
    MessageItem,
)
from core.llm import LLMError

router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    return HealthResponse(status="ok", app="MAXY", model=settings.ollama_model)


@router.get("/conversations", response_model=list[ConversationSummary])
async def conversations(request: Request) -> list[dict[str, str]]:
    return request.app.state.store.list_conversations()


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageItem],
)
async def conversation_messages(
    conversation_id: str, request: Request
) -> list[dict[str, str]]:
    store = request.app.state.store
    if not store.conversation_exists(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )
    return store.get_messages(conversation_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    service = request.app.state.assistant
    store = request.app.state.store
    conversation_id = payload.conversation_id

    if conversation_id is None:
        conversation_id = service.create_conversation(payload.message)
    elif not store.conversation_exists(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found.",
        )

    try:
        reply = await service.reply(conversation_id, payload.message)
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
            headers={"X-Conversation-ID": conversation_id},
        ) from exc

    return ChatResponse(conversation_id=conversation_id, reply=reply)

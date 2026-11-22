"""HTTP routes for the MAXY text assistant."""
from fastapi import APIRouter, HTTPException, Request, status

from api.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationSummary,
    HealthResponse,
    MessageItem,
    MemoryCreate,
    TaskCreate,
    TaskStatusUpdate,
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
        reply, proposal = await service.reply_with_action(
            conversation_id, payload.message, request.app.state.approvals
        )
    except LLMError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
            headers={"X-Conversation-ID": conversation_id},
        ) from exc

    pending_action = None
    if proposal:
        pending_action = {
            key: proposal[key]
            for key in ("proposal_id", "tool_name", "arguments", "preview", "expires_at", "approval_phrase")
        }
    return ChatResponse(
        conversation_id=conversation_id, reply=reply, pending_action=pending_action
    )


@router.get("/memory")
async def list_memory(request: Request) -> list[dict[str, str]]:
    return request.app.state.store.list_memories()


@router.post("/memory", status_code=status.HTTP_201_CREATED)
async def create_memory(payload: MemoryCreate, request: Request) -> dict[str, str]:
    try:
        return request.app.state.store.save_memory(payload.content, payload.category)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str, request: Request) -> dict[str, bool]:
    if not request.app.state.store.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"deleted": True}


@router.delete("/memory")
async def clear_memory(request: Request) -> dict[str, int]:
    return {"deleted": request.app.state.store.clear_memories()}


@router.get("/tasks")
async def list_tasks(request: Request, include_completed: bool = True) -> list[dict[str, str]]:
    return request.app.state.store.list_tasks(include_completed=include_completed)


@router.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, request: Request) -> dict[str, str]:
    try:
        return request.app.state.store.create_task(payload.title, payload.due_at)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.patch("/tasks/{task_id}")
async def update_task(task_id: str, payload: TaskStatusUpdate, request: Request) -> dict[str, bool]:
    if not request.app.state.store.set_task_status(task_id, payload.status):
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"updated": True}


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, request: Request) -> dict[str, bool]:
    if not request.app.state.store.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found.")
    return {"deleted": True}

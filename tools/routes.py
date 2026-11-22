"""Explicit tool discovery and user approval endpoints."""
from fastapi import APIRouter, HTTPException, Request

from tools.registry import ToolError
from tools.schemas import ToolApprovalRequest, ToolProposalRequest

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("")
async def list_tools(request: Request) -> dict:
    return {"tools": request.app.state.tool_registry.descriptions()}


@router.post("/proposals")
async def create_proposal(payload: ToolProposalRequest, request: Request) -> dict:
    try:
        return request.app.state.approvals.propose(payload.tool_name, payload.arguments)
    except ToolError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: str, payload: ToolApprovalRequest,
                           request: Request) -> dict:
    try:
        return request.app.state.approvals.approve_and_execute(
            proposal_id, payload.approval_phrase
        )
    except ToolError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

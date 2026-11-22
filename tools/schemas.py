"""Validated payloads for permission-gated tools."""
from pydantic import BaseModel, Field, field_validator


class ToolProposalRequest(BaseModel):
    tool_name: str = Field(min_length=1, max_length=64)
    arguments: dict = Field(default_factory=dict)


class ToolApprovalRequest(BaseModel):
    approval_phrase: str = Field(min_length=1, max_length=32)

    @field_validator("approval_phrase")
    @classmethod
    def normalize_phrase(cls, value: str) -> str:
        return value.strip().upper()

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AgentContract(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProposedAction(AgentContract):
    tool_name: str
    arguments: dict[str, Any]
    call_id: str | None = None
    requires_confirmation: bool = False


class MemoryDocument(AgentContract):
    key: str
    kind: Literal["semantic", "procedural"]
    content: str = Field(min_length=1, max_length=500)
    source_thread: str
    source_turn: str
    created_at: datetime
    updated_at: datetime
    confidence: float = Field(ge=0, le=1)
    explicit_user: bool = False


class ChatResume(AgentContract):
    value: Any


class ChatRequest(AgentContract):
    conversation_id: str = Field(min_length=1, max_length=200)
    message: str | None = Field(default=None, min_length=1, max_length=20_000)
    request_id: str = Field(min_length=1, max_length=200)
    locale: str = Field(default="es", max_length=32)
    timezone: str = Field(default="UTC", max_length=100)
    resume: ChatResume | None = None

    @model_validator(mode="after")
    def exactly_one_input(self) -> "ChatRequest":
        if (self.message is None) == (self.resume is None):
            raise ValueError("provide exactly one of message or resume")
        return self


class ChatInterrupt(AgentContract):
    id: str
    kind: str
    question: str
    details: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(AgentContract):
    conversation_id: str
    status: Literal["completed", "needs_user_response", "blocked", "error"]
    message: str
    interrupt: ChatInterrupt | None = None
    tool: dict[str, Any] | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    trace_id: str | None = None

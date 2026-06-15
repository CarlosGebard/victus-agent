from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.events.models import SafetyStatus, ToolEventRef

ToolStatus = Literal["success", "needs_clarification", "blocked", "rejected", "error"]
ExpectedAnswerType = Literal[
    "quantity",
    "time",
    "meal_reference",
    "preference_strength",
    "restriction_type",
    "goal_target",
    "yes_no",
    "free_text",
]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClarificationRequest(ContractModel):
    missing_fields: list[str]
    question: str
    expected_answer_type: ExpectedAnswerType
    resume_node: str | None = None
    resume_action: str | None = None


class ToolSafety(ContractModel):
    status: SafetyStatus
    reasons: list[str] = Field(default_factory=list)


class ToolMeta(ContractModel):
    confidence: float | None = None
    schema_version: Literal[1] = 1
    handler_version: str | None = None
    trace_id: str | None = None


class ToolResult(ContractModel):
    status: ToolStatus
    data: Any | None = None
    events_emitted: list[ToolEventRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    clarification: ClarificationRequest | None = None
    safety: ToolSafety = Field(default_factory=lambda: ToolSafety(status="ok"))
    meta: ToolMeta = Field(default_factory=ToolMeta)

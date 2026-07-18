from __future__ import annotations

from typing import Literal

from pydantic import Field

from domain.events.base import ContractModel
from tools.contracts import ExpectedAnswerType


class ClarificationInput(ContractModel):
    user_id: str
    action: Literal["request", "resolve"]
    clarification_id: str | None = None
    blocked_node: str | None = None
    blocked_action: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    question: str | None = None
    expected_answer_type: ExpectedAnswerType | None = None
    answer: str | None = None
    resume_node: str | None = None
    resume_action: str | None = None


class ConfirmationInput(ContractModel):
    user_id: str
    action: Literal["request", "resolve"]
    confirmation_id: str | None = None
    blocked_node: str | None = None
    blocked_action: str | None = None
    question: str | None = None
    risk_level: Literal["low", "medium", "high", "critical"] | None = None
    accepted: bool | None = None
    answer: str | None = None
    resume_node: str | None = None
    resume_action: str | None = None

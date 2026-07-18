from __future__ import annotations

from domain.events.base import ContractModel


class ClarificationRequestedPayload(ContractModel):
    clarification_id: str
    blocked_node: str | None = None
    blocked_action: str | None = None
    missing_fields: list[str]
    question: str
    expected_answer_type: str


class ClarificationResolvedPayload(ContractModel):
    clarification_id: str
    answer: str
    resume_node: str | None = None
    resume_action: str | None = None


class ConfirmationRequestedPayload(ContractModel):
    confirmation_id: str
    blocked_node: str | None = None
    blocked_action: str | None = None
    question: str
    risk_level: str
    expected_answer_type: str = "yes_no"


class ConfirmationResolvedPayload(ContractModel):
    confirmation_id: str
    accepted: bool
    answer: str | None = None
    resume_node: str | None = None
    resume_action: str | None = None

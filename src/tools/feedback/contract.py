from __future__ import annotations

from typing import Literal

from domain.events.base import ContractModel

FeedbackAction = Literal["record", "resolve"]


class FeedbackInput(ContractModel):
    user_id: str
    action: FeedbackAction
    feedback_id: str | None = None
    target_type: Literal["plan", "meal", "recommendation", "answer", "other"] | None = None
    target_id: str | None = None
    sentiment: Literal["positive", "neutral", "negative", "mixed"] | None = None
    text: str | None = None
    resolution: Literal["accepted", "rejected", "incorporated", "needs_more_info"] | None = None
    linked_revision_id: str | None = None


FeedbackDecision = FeedbackInput

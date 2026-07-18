from __future__ import annotations

from typing import Literal

from domain.events.base import ContractModel


class FeedbackRecordedPayload(ContractModel):
    feedback_id: str
    target_type: Literal["plan", "meal", "recommendation", "answer", "other"]
    target_id: str | None = None
    sentiment: Literal["positive", "neutral", "negative", "mixed"] | None = None
    text: str


class FeedbackResolvedPayload(ContractModel):
    feedback_id: str
    resolution: Literal["accepted", "rejected", "incorporated", "needs_more_info"]
    linked_revision_id: str | None = None

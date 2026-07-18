from __future__ import annotations

from pydantic import Field

from domain.projections.models.base import ContractModel


class RevisionSummary(ContractModel):
    revision_id: str
    session_id: str
    created_at: str
    summary: str | None = None


class FeedbackSummary(ContractModel):
    feedback_id: str
    target_type: str
    target_id: str | None = None
    sentiment: str | None = None
    resolved: bool | None = None


class PlanningHistoryProjection(ContractModel):
    user_id: str
    active_session_id: str | None = None
    active_plan_artifact_id: str | None = None
    active_goal_id: str | None = None
    revision_summary: list[RevisionSummary] = Field(default_factory=list)
    feedback_summary: list[FeedbackSummary] = Field(default_factory=list)
    last_event_seq: int
    updated_at: str

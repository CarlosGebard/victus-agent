from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from domain.projections.models.planning_history import (
    FeedbackSummary,
    PlanningHistoryProjection,
    RevisionSummary,
)
from domain.projections.projectors._common import now_iso

PLANNING_HISTORY_PROJECTOR = "planning_history"


def apply_planning_history_event(
    projection: PlanningHistoryProjection | None,
    event: UserEventEnvelope,
) -> PlanningHistoryProjection:
    current = projection or PlanningHistoryProjection(
        user_id=event.user_id,
        last_event_seq=0,
        updated_at=now_iso(),
    )
    payload = event.payload
    if event.event_type in {"goal.set", "goal.adjusted"}:
        current.active_goal_id = payload["goal_id"]
    elif event.event_type == "plan.session_started":
        current.active_session_id = payload["session_id"]
        if payload.get("goal_id"):
            current.active_goal_id = payload["goal_id"]
    elif event.event_type == "plan.revision_created":
        summary = RevisionSummary(
            revision_id=payload["revision_id"],
            session_id=payload["session_id"],
            created_at=event.occurred_at,
            summary=payload.get("summary"),
        )
        current.revision_summary = [
            item for item in current.revision_summary if item.revision_id != summary.revision_id
        ]
        current.revision_summary.insert(0, summary)
        current.revision_summary = current.revision_summary[:50]
    elif event.event_type == "plan.artifact_saved":
        current.active_plan_artifact_id = payload["artifact_id"]
    elif event.event_type == "plan.session_ended":
        if current.active_session_id == payload["session_id"]:
            current.active_session_id = None
    elif event.event_type == "feedback.recorded":
        feedback = FeedbackSummary(
            feedback_id=payload["feedback_id"],
            target_type=payload["target_type"],
            target_id=payload.get("target_id"),
            sentiment=payload.get("sentiment"),
            resolved=False,
        )
        current.feedback_summary = [
            item for item in current.feedback_summary if item.feedback_id != feedback.feedback_id
        ]
        current.feedback_summary.insert(0, feedback)
        current.feedback_summary = current.feedback_summary[:50]
    elif event.event_type == "feedback.resolved":
        for feedback in current.feedback_summary:
            if feedback.feedback_id == payload["feedback_id"]:
                feedback.resolved = True

    current.last_event_seq = max(current.last_event_seq, event.event_seq)
    current.updated_at = now_iso()
    return current

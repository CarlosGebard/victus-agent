from __future__ import annotations

from domain.events.feedback import FeedbackResolvedPayload
from tools._event_builder import tool_event_envelope
from tools.feedback.contract import FeedbackDecision, FeedbackInput


def build_resolve_event(*, decision: FeedbackDecision, input: FeedbackInput):
    feedback_id = decision.feedback_id or "unknown"
    payload = FeedbackResolvedPayload(
        feedback_id=feedback_id,
        resolution=decision.resolution or "needs_more_info",
        linked_revision_id=decision.linked_revision_id,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="feedback",
        event_type="feedback.resolved",
        aggregate_type="feedback",
        aggregate_id=feedback_id,
        actor_id="feedback.resolve",
        payload=payload,
        idempotency_key=f"feedback:resolve:{input.user_id}:{feedback_id}:{decision.resolution}",
    )

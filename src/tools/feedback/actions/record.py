from __future__ import annotations

from domain.events.feedback import FeedbackRecordedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.feedback.contract import FeedbackDecision, FeedbackInput


def build_record_event(*, decision: FeedbackDecision, input: FeedbackInput):
    feedback_id = decision.feedback_id or new_prefixed_id("feedback")
    payload = FeedbackRecordedPayload(
        feedback_id=feedback_id,
        target_type=decision.target_type or "other",
        target_id=decision.target_id,
        sentiment=decision.sentiment,
        text=decision.text or "",
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="feedback",
        event_type="feedback.recorded",
        aggregate_type="feedback",
        aggregate_id=feedback_id,
        actor_id="feedback.record",
        payload=payload,
        idempotency_key=f"feedback:record:{input.user_id}:{feedback_id}",
    )

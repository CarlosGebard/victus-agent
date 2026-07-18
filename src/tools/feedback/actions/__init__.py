from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from tools.feedback.actions.record import build_record_event
from tools.feedback.actions.resolve import build_resolve_event
from tools.feedback.contract import FeedbackDecision, FeedbackInput


def build_feedback_event(*, decision: FeedbackDecision, input: FeedbackInput) -> UserEventEnvelope:
    if decision.action == "record":
        return build_record_event(decision=decision, input=input)
    return build_resolve_event(decision=decision, input=input)

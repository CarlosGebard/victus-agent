from __future__ import annotations

from domain.events.planning import PlanSessionEndedPayload
from tools._event_builder import tool_event_envelope
from tools.planning.contract import PlanningDecision, PlanningInput


def build_end_session_event(*, decision: PlanningDecision, input: PlanningInput):
    session_id = decision.session_id or "unknown"
    payload = PlanSessionEndedPayload(
        session_id=session_id,
        status=decision.status or "completed",
        reason=decision.reason,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="planning",
        event_type="plan.session_ended",
        aggregate_type="plan_session",
        aggregate_id=session_id,
        actor_id=f"planning.{decision.action}",
        payload=payload,
        idempotency_key=f"planning:end_session:{input.user_id}:{session_id}:{decision.status}",
    )

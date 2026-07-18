from __future__ import annotations

from domain.events.planning import PlanSessionStartedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.planning.contract import PlanningDecision, PlanningInput


def build_start_session_event(*, decision: PlanningDecision, input: PlanningInput):
    session_id = decision.session_id or new_prefixed_id("plan_session")
    payload = PlanSessionStartedPayload(
        session_id=session_id,
        reason=decision.reason or "planning_requested",
        goal_id=decision.goal_id,
        active_plan_id=decision.active_plan_id,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="planning",
        event_type="plan.session_started",
        aggregate_type="plan_session",
        aggregate_id=session_id,
        actor_id=f"planning.{decision.action}",
        payload=payload,
        idempotency_key=f"planning:start_session:{input.user_id}:{session_id}",
    )

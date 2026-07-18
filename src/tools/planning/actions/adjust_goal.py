from __future__ import annotations

from domain.events.planning import GoalAdjustedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.planning.contract import PlanningDecision, PlanningInput


def build_adjust_goal_event(*, decision: PlanningDecision, input: PlanningInput):
    goal_id = decision.goal_id or new_prefixed_id("goal")
    payload = GoalAdjustedPayload(
        goal_id=goal_id,
        patch=decision.patch or {},
        reason=decision.reason,
        user_confirmed=decision.user_confirmed,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="planning",
        event_type="goal.adjusted",
        aggregate_type="goal",
        aggregate_id=goal_id,
        actor_id=f"planning.{decision.action}",
        payload=payload,
        idempotency_key=f"planning:adjust_goal:{input.user_id}:{goal_id}:{hash(str(decision.patch))}",
    )

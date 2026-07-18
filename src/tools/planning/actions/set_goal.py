from __future__ import annotations

from domain.events.planning import GoalSetPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.planning.contract import PlanningDecision, PlanningInput


def build_set_goal_event(*, decision: PlanningDecision, input: PlanningInput):
    goal_id = decision.goal_id or new_prefixed_id("goal")
    payload = GoalSetPayload(
        goal_id=goal_id,
        primary_goal=decision.primary_goal or "unknown",
        horizon_weeks=decision.horizon_weeks,
        energy_target=decision.energy_target,
        macro_targets=decision.macro_targets,
        user_confirmed=decision.user_confirmed,
    )
    return tool_event_envelope(
        user_id=input.user_id,
        tool_name="planning",
        event_type="goal.set",
        aggregate_type="goal",
        aggregate_id=goal_id,
        actor_id=f"planning.{decision.action}",
        payload=payload,
        idempotency_key=f"planning:set_goal:{input.user_id}:{goal_id}",
    )

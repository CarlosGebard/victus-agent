from __future__ import annotations

from tools.planning.contract import PlanningDecision, PlanningInput


def decide_with_policy(input: PlanningInput) -> PlanningDecision:
    if input.action == "set_goal" and not input.primary_goal:
        raise PlanningPolicyError("set_goal requires primary_goal")
    if input.action == "adjust_goal" and not input.patch:
        raise PlanningPolicyError("adjust_goal requires patch")
    if input.action in {"end_session"} and not input.session_id:
        raise PlanningPolicyError("end_session requires session_id")
    return input


class PlanningPolicyError(ValueError):
    pass

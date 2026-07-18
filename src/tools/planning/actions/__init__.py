from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from tools.planning.actions.adjust_goal import build_adjust_goal_event
from tools.planning.actions.create_revision import build_create_revision_event
from tools.planning.actions.end_session import build_end_session_event
from tools.planning.actions.save_artifact import build_save_artifact_event
from tools.planning.actions.set_goal import build_set_goal_event
from tools.planning.actions.start_session import build_start_session_event
from tools.planning.contract import PlanningDecision, PlanningInput


def build_planning_event(
    *,
    decision: PlanningDecision,
    input: PlanningInput,
) -> UserEventEnvelope:
    builders = {
        "set_goal": build_set_goal_event,
        "adjust_goal": build_adjust_goal_event,
        "start_session": build_start_session_event,
        "create_revision": build_create_revision_event,
        "save_artifact": build_save_artifact_event,
        "end_session": build_end_session_event,
    }
    return builders[decision.action](decision=decision, input=input)

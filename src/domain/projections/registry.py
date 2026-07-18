from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from domain.events.envelope import UserEventEnvelope
from domain.projections.projectors import (
    CONSTRAINT_PROJECTOR,
    NUTRITION_STATUS_PROJECTOR,
    PLANNING_HISTORY_PROJECTOR,
    USER_PROFILE_PROJECTOR,
    apply_constraint_event,
    apply_nutrition_status_event,
    apply_planning_history_event,
    apply_user_profile_event,
)

ProjectorApply = Callable[[object | None, UserEventEnvelope], object]


@dataclass(frozen=True)
class ProjectionDefinition:
    name: str
    events: frozenset[str]
    apply: ProjectorApply


PROJECTION_REGISTRY = {
    USER_PROFILE_PROJECTOR: ProjectionDefinition(
        name=USER_PROFILE_PROJECTOR,
        events=frozenset({"restriction.added", "preference.updated", "goal.set", "goal.adjusted"}),
        apply=apply_user_profile_event,
    ),
    NUTRITION_STATUS_PROJECTOR: ProjectionDefinition(
        name=NUTRITION_STATUS_PROJECTOR,
        events=frozenset(
            {
                "meal.logged",
                "meal.deleted",
                "biometrics.logged",
                "lifestyle_metric.logged",
                "symptom.logged",
            }
        ),
        apply=apply_nutrition_status_event,
    ),
    CONSTRAINT_PROJECTOR: ProjectionDefinition(
        name=CONSTRAINT_PROJECTOR,
        events=frozenset(
            {
                "restriction.added",
                "preference.updated",
                "safety.guard_triggered",
                "safety.action_blocked",
            }
        ),
        apply=apply_constraint_event,
    ),
    PLANNING_HISTORY_PROJECTOR: ProjectionDefinition(
        name=PLANNING_HISTORY_PROJECTOR,
        events=frozenset(
            {
                "goal.set",
                "goal.adjusted",
                "plan.session_started",
                "plan.revision_created",
                "plan.artifact_saved",
                "plan.session_ended",
                "feedback.recorded",
                "feedback.resolved",
            }
        ),
        apply=apply_planning_history_event,
    ),
}


def events_for_projector(name: str) -> frozenset[str]:
    return PROJECTION_REGISTRY[name].events

from __future__ import annotations

from events.repository import PostgresEventStore
from projections.projectors import (
    CONSTRAINT_PROJECTOR,
    NUTRITION_STATUS_PROJECTOR,
    PLANNING_HISTORY_PROJECTOR,
    USER_PROFILE_PROJECTOR,
    apply_constraint_event,
    apply_nutrition_status_event,
    apply_planning_history_event,
    apply_user_profile_event,
)
from projections.repository import ProjectionRepository

USER_PROFILE_EVENTS = {"restriction.added", "preference.updated", "goal.set", "goal.adjusted"}
NUTRITION_STATUS_EVENTS = {"meal.logged", "meal.deleted", "biometrics.logged", "symptom.logged"}
CONSTRAINT_EVENTS = {
    "restriction.added",
    "preference.updated",
    "safety.guard_triggered",
    "safety.action_blocked",
}
PLANNING_HISTORY_EVENTS = {
    "goal.set",
    "goal.adjusted",
    "plan.session_started",
    "plan.revision_created",
    "plan.artifact_saved",
    "plan.session_ended",
    "feedback.recorded",
    "feedback.resolved",
}


def rebuild_user_profile(
    *,
    user_id: str,
    event_store: PostgresEventStore,
    projections: ProjectionRepository,
    limit: int = 500,
) -> int:
    current = projections.get_user_profile(user_id)
    processed = 0
    after_seq = 0
    while True:
        events = event_store.list_for_user(user_id, after_seq=after_seq, limit=limit)
        if not events:
            break
        for event in events:
            after_seq = event.event_seq
            if event.event_type in USER_PROFILE_EVENTS:
                current = apply_user_profile_event(current, event)
                processed = event.event_seq
        if len(events) < limit:
            break
    if current is not None:
        projections.save_user_profile(current)
        projections.save_offset(USER_PROFILE_PROJECTOR, current.last_event_seq)
    return processed


def rebuild_nutrition_status(
    *,
    user_id: str,
    event_store: PostgresEventStore,
    projections: ProjectionRepository,
    limit: int = 500,
) -> int:
    current = None
    processed = 0
    after_seq = 0
    while True:
        events = event_store.list_for_user(user_id, after_seq=after_seq, limit=limit)
        if not events:
            break
        for event in events:
            after_seq = event.event_seq
            if event.event_type in NUTRITION_STATUS_EVENTS:
                current = apply_nutrition_status_event(current, event)
                processed = event.event_seq
        if len(events) < limit:
            break
    if current is not None:
        projections.save_nutrition_status(current)
        projections.save_offset(NUTRITION_STATUS_PROJECTOR, current.last_event_seq)
    return processed


def rebuild_constraint(
    *,
    user_id: str,
    event_store: PostgresEventStore,
    projections: ProjectionRepository,
    limit: int = 500,
) -> int:
    current = projections.get_constraint(user_id)
    after_seq = 0
    while True:
        events = event_store.list_for_user(user_id, after_seq=after_seq, limit=limit)
        if not events:
            break
        for event in events:
            after_seq = event.event_seq
            if event.event_type in CONSTRAINT_EVENTS:
                current = apply_constraint_event(current, event)
        if len(events) < limit:
            break
    if current is not None:
        projections.save_constraint(current)
        projections.save_offset(CONSTRAINT_PROJECTOR, current.derived_from_event_seq)
        return current.derived_from_event_seq
    return 0


def rebuild_planning_history(
    *,
    user_id: str,
    event_store: PostgresEventStore,
    projections: ProjectionRepository,
    limit: int = 500,
) -> int:
    current = projections.get_planning_history(user_id)
    after_seq = 0
    while True:
        events = event_store.list_for_user(user_id, after_seq=after_seq, limit=limit)
        if not events:
            break
        for event in events:
            after_seq = event.event_seq
            if event.event_type in PLANNING_HISTORY_EVENTS:
                current = apply_planning_history_event(current, event)
        if len(events) < limit:
            break
    if current is not None:
        projections.save_planning_history(current)
        projections.save_offset(PLANNING_HISTORY_PROJECTOR, current.last_event_seq)
        return current.last_event_seq
    return 0


def rebuild_all_for_user(
    *,
    user_id: str,
    event_store: PostgresEventStore,
    projections: ProjectionRepository,
) -> dict[str, int]:
    return {
        USER_PROFILE_PROJECTOR: rebuild_user_profile(
            user_id=user_id,
            event_store=event_store,
            projections=projections,
        ),
        NUTRITION_STATUS_PROJECTOR: rebuild_nutrition_status(
            user_id=user_id,
            event_store=event_store,
            projections=projections,
        ),
        CONSTRAINT_PROJECTOR: rebuild_constraint(
            user_id=user_id,
            event_store=event_store,
            projections=projections,
        ),
        PLANNING_HISTORY_PROJECTOR: rebuild_planning_history(
            user_id=user_id,
            event_store=event_store,
            projections=projections,
        ),
    }

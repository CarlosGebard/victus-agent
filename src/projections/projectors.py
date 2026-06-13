from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from events.models import UserEventEnvelope
from projections.models import (
    BiometricSummary,
    BiometricValue,
    ConstraintProjection,
    FeedbackSummary,
    HardConstraint,
    NutritionStatusProjection,
    PlanningHistoryProjection,
    PreferenceView,
    RecentMeal,
    RecentMealItem,
    RestrictionView,
    RevisionSummary,
    SafetyFlag,
    SoftConstraint,
    SymptomView,
    UserProfileProjection,
)


USER_PROFILE_PROJECTOR = "user_profile"
NUTRITION_STATUS_PROJECTOR = "nutrition_status"
CONSTRAINT_PROJECTOR = "constraint"
PLANNING_HISTORY_PROJECTOR = "planning_history"


def apply_user_profile_event(
    projection: UserProfileProjection | None,
    event: UserEventEnvelope,
) -> UserProfileProjection:
    current = projection or UserProfileProjection(
        user_id=event.user_id,
        last_event_seq=0,
        updated_at=_now(),
    )
    if event.event_type == "restriction.added":
        payload = event.payload
        restriction = RestrictionView(
            restriction_id=payload["restriction_id"],
            kind=payload["restriction_kind"],
            label=payload["restricted_substance_label"],
            severity=payload["severity"],
            metadata={
                "condition_label": payload.get("condition_label"),
                "scope": payload.get("scope"),
                "evidence_level": payload.get("evidence_level"),
            },
        )
        current.restrictions = [
            item for item in current.restrictions if item.restriction_id != restriction.restriction_id
        ]
        current.restrictions.append(restriction)
    elif event.event_type == "preference.updated":
        payload = event.payload
        preference = PreferenceView(
            preference_id=payload["preference_id"],
            category=payload["category"],
            item_label=payload["item_label"],
            preference=payload["preference"],
            strength=payload["strength"],
        )
        current.preferences = [
            item for item in current.preferences if item.preference_id != preference.preference_id
        ]
        current.preferences.append(preference)
    elif event.event_type in {"goal.set", "goal.adjusted"}:
        current.active_goal_id = event.payload["goal_id"]

    current.last_event_seq = max(current.last_event_seq, event.event_seq)
    current.updated_at = _now()
    return current


def apply_nutrition_status_event(
    projection: NutritionStatusProjection | None,
    event: UserEventEnvelope,
) -> NutritionStatusProjection:
    current = projection or NutritionStatusProjection(
        user_id=event.user_id,
        last_event_seq=0,
        updated_at=_now(),
    )
    if event.event_type == "meal.logged":
        payload = event.payload
        meal = RecentMeal(
            meal_id=payload["meal_id"],
            meal_type=payload["meal_type"],
            consumed_at=payload["consumed_at"],
            items=[
                RecentMealItem(
                    item_id=item["item_id"],
                    food_label=item["food_label"],
                    quantity=item.get("quantity"),
                )
                for item in payload["items"]
            ],
            status="active",
        )
        current.recent_meals = [item for item in current.recent_meals if item.meal_id != meal.meal_id]
        current.recent_meals.insert(0, meal)
        current.recent_meals = current.recent_meals[:50]
    elif event.event_type == "meal.deleted":
        meal_id = event.payload["meal_id"]
        for meal in current.recent_meals:
            if meal.meal_id == meal_id:
                meal.status = "deleted"
    elif event.event_type == "biometrics.logged":
        current.biometrics = _apply_biometrics(current.biometrics, event.payload)
    elif event.event_type == "symptom.logged":
        payload = event.payload
        current.symptoms = [
            item for item in current.symptoms if item.symptom_id != payload["symptom_id"]
        ]
        current.symptoms.insert(
            0,
            SymptomView(
                symptom_id=payload["symptom_id"],
                label=payload["label"],
                severity=payload.get("severity"),
                occurred_at=payload["occurred_at"],
            ),
        )
        current.symptoms = current.symptoms[:50]

    current.last_event_seq = max(current.last_event_seq, event.event_seq)
    current.updated_at = _now()
    return current


def apply_constraint_event(
    projection: ConstraintProjection | None,
    event: UserEventEnvelope,
) -> ConstraintProjection:
    current = projection or ConstraintProjection(
        user_id=event.user_id,
        derived_from_event_seq=0,
        updated_at=_now(),
    )
    payload = event.payload
    if event.event_type == "restriction.added":
        kind = payload["restriction_kind"]
        constraint = HardConstraint(
            constraint_id=payload["restriction_id"],
            kind=kind if kind in {"allergy", "medical", "religious"} else "safety",
            label=payload["restricted_substance_label"],
            severity=payload["severity"],
            rule={
                "scope": payload["scope"],
                "evidence_level": payload["evidence_level"],
                "condition_label": payload.get("condition_label"),
            },
        )
        current.hard_constraints = [
            item for item in current.hard_constraints if item.constraint_id != constraint.constraint_id
        ]
        current.hard_constraints.append(constraint)
    elif event.event_type == "preference.updated":
        constraint = SoftConstraint(
            constraint_id=payload["preference_id"],
            kind=_soft_constraint_kind(payload["category"]),
            label=payload["item_label"],
            strength=payload["strength"],
            rule={"preference": payload["preference"], "category": payload["category"]},
        )
        current.soft_constraints = [
            item for item in current.soft_constraints if item.constraint_id != constraint.constraint_id
        ]
        current.soft_constraints.append(constraint)
    elif event.event_type in {"safety.guard_triggered", "safety.action_blocked"}:
        flag = SafetyFlag(
            flag_id=f"{event.event_type}:{event.event_seq}",
            risk_category=payload["risk_category"],
            status=payload.get("safety_status", "blocked"),
            reasons=payload["reasons"],
        )
        current.safety_flags.insert(0, flag)
        current.safety_flags = current.safety_flags[:50]

    current.derived_from_event_seq = max(current.derived_from_event_seq, event.event_seq)
    current.updated_at = _now()
    return current


def apply_planning_history_event(
    projection: PlanningHistoryProjection | None,
    event: UserEventEnvelope,
) -> PlanningHistoryProjection:
    current = projection or PlanningHistoryProjection(
        user_id=event.user_id,
        last_event_seq=0,
        updated_at=_now(),
    )
    payload = event.payload
    if event.event_type in {"goal.set", "goal.adjusted"}:
        current.active_goal_id = payload["goal_id"]
    elif event.event_type == "plan.session_started":
        current.active_session_id = payload["session_id"]
        if payload.get("goal_id"):
            current.active_goal_id = payload["goal_id"]
    elif event.event_type == "plan.revision_created":
        summary = RevisionSummary(
            revision_id=payload["revision_id"],
            session_id=payload["session_id"],
            created_at=event.occurred_at,
            summary=payload.get("summary"),
        )
        current.revision_summary = [
            item for item in current.revision_summary if item.revision_id != summary.revision_id
        ]
        current.revision_summary.insert(0, summary)
        current.revision_summary = current.revision_summary[:50]
    elif event.event_type == "plan.artifact_saved":
        current.active_plan_artifact_id = payload["artifact_id"]
    elif event.event_type == "plan.session_ended":
        if current.active_session_id == payload["session_id"]:
            current.active_session_id = None
    elif event.event_type == "feedback.recorded":
        feedback = FeedbackSummary(
            feedback_id=payload["feedback_id"],
            target_type=payload["target_type"],
            target_id=payload.get("target_id"),
            sentiment=payload.get("sentiment"),
            resolved=False,
        )
        current.feedback_summary = [
            item for item in current.feedback_summary if item.feedback_id != feedback.feedback_id
        ]
        current.feedback_summary.insert(0, feedback)
        current.feedback_summary = current.feedback_summary[:50]
    elif event.event_type == "feedback.resolved":
        for feedback in current.feedback_summary:
            if feedback.feedback_id == payload["feedback_id"]:
                feedback.resolved = True

    current.last_event_seq = max(current.last_event_seq, event.event_seq)
    current.updated_at = _now()
    return current


def _apply_biometrics(summary: BiometricSummary, payload: dict[str, Any]) -> BiometricSummary:
    for measurement in payload["measurements"]:
        value = BiometricValue(
            value=measurement["value"],
            unit=measurement["unit"],
            measured_at=payload["measured_at"],
        )
        if measurement["type"] == "weight":
            summary.latest_weight = value
        elif measurement["type"] == "height":
            summary.latest_height = value
        elif measurement["type"] == "sleep":
            summary.sleep = measurement
        elif measurement["type"] == "steps":
            summary.steps = measurement
    return summary


def _soft_constraint_kind(category: str) -> str:
    if category in {"budget", "schedule", "cooking"}:
        return category
    return "preference"


def _now() -> str:
    return datetime.now(UTC).isoformat()

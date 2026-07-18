from __future__ import annotations

from typing import Any

from domain.events.envelope import UserEventEnvelope
from domain.projections.models.nutrition_status import (
    BiometricSummary,
    BiometricValue,
    NutritionStatusProjection,
    RecentMeal,
    RecentMealItem,
    SymptomView,
)
from domain.projections.projectors._common import now_iso

NUTRITION_STATUS_PROJECTOR = "nutrition_status"


def apply_nutrition_status_event(
    projection: NutritionStatusProjection | None,
    event: UserEventEnvelope,
) -> NutritionStatusProjection:
    current = projection or NutritionStatusProjection(
        user_id=event.user_id,
        last_event_seq=0,
        updated_at=now_iso(),
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
    elif event.event_type == "lifestyle_metric.logged":
        current.biometrics = _apply_lifestyle_metric(current.biometrics, event.payload)
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
    current.updated_at = now_iso()
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


def _apply_lifestyle_metric(summary: BiometricSummary, payload: dict[str, Any]) -> BiometricSummary:
    metric = payload["metric"]
    if metric == "sleep_duration":
        summary.sleep = payload
    elif metric == "steps":
        summary.steps = payload
    return summary

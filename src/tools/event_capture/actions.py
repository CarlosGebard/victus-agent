from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from domain.events.envelope import EventActor, EventMetadata, UserEventEnvelope
from domain.events.health_metrics import (
    BiometricMeasurement,
    BiometricsLoggedPayload,
    LifestyleMetricLoggedPayload,
    SymptomLoggedPayload,
)
from domain.events.nutrition import MealItem, MealLoggedPayload
from tools.event_capture.contract import EventCaptureDecision, EventCaptureInput


def build_event_capture_event(
    *, decision: EventCaptureDecision, input: EventCaptureInput
) -> UserEventEnvelope | None:
    if decision.requires_safety_validation:
        return None
    builders = {
        "log_meal": _build_meal,
        "log_biometrics": _build_biometrics,
        "log_lifestyle_metric": _build_lifestyle,
        "log_symptom": _build_symptom,
    }
    builder = builders.get(decision.capture_action)
    return builder(decision, input) if builder else None


def _build_meal(decision: EventCaptureDecision, input: EventCaptureInput) -> UserEventEnvelope:
    meal_id = _new_id("meal")
    occurred_at = _now()
    raw_meal = decision.extracted.get("meal", {})
    meal = raw_meal if isinstance(raw_meal, dict) else {}
    raw_items = meal.get("items", [])
    items = raw_items if isinstance(raw_items, list) else []
    payload = MealLoggedPayload(
        meal_id=meal_id,
        meal_type=_meal_type(meal.get("meal_type")),
        consumed_at=occurred_at,
        source="manual",
        items=[
            MealItem(
                item_id=_new_id("meal_item"),
                food_label=str(item["name"]),
                quantity=_numeric_quantity(item.get("quantity_text")),
            )
            for item in items
            if isinstance(item, dict) and item.get("name")
        ],
        notes=_note(decision.reason, decision.occurred_at_text),
    )
    return _envelope(
        input=input,
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id=meal_id,
        actor_id="nutrition.log_meal",
        payload=payload,
        occurred_at=occurred_at,
    )


def _build_biometrics(
    decision: EventCaptureDecision, input: EventCaptureInput
) -> UserEventEnvelope:
    measurement_id = _new_id("measurement")
    occurred_at = _now()
    raw = decision.extracted.get("biometrics", {})
    data = raw if isinstance(raw, dict) else {}
    payload = BiometricsLoggedPayload(
        measurement_id=measurement_id,
        measured_at=occurred_at,
        measurements=_measurements(data),
        source="manual",
    )
    return _envelope(
        input=input,
        event_type="biometrics.logged",
        aggregate_type="biometrics",
        aggregate_id=measurement_id,
        actor_id="biometrics.log",
        payload=payload,
        occurred_at=occurred_at,
    )


def _build_lifestyle(
    decision: EventCaptureDecision, input: EventCaptureInput
) -> UserEventEnvelope:
    metric_id = _new_id("lifestyle_metric")
    occurred_at = _now()
    raw = decision.extracted.get("lifestyle_metric", {})
    data = raw if isinstance(raw, dict) else {}
    metric = str(data.get("metric") or "energy")
    allowed = {"sleep_duration", "water_intake", "steps", "stress", "energy", "hunger"}
    payload = LifestyleMetricLoggedPayload(
        metric_id=metric_id,
        occurred_at=occurred_at,
        metric=metric if metric in allowed else "energy",
        value=data.get("value"),
        unit=str(data["unit"]) if data.get("unit") else None,
        raw_value_text=str(data["raw_value_text"]) if data.get("raw_value_text") else None,
        source="manual",
    )
    return _envelope(
        input=input,
        event_type="lifestyle_metric.logged",
        aggregate_type="lifestyle_metric",
        aggregate_id=metric_id,
        actor_id="lifestyle.log",
        payload=payload,
        occurred_at=occurred_at,
    )


def _build_symptom(
    decision: EventCaptureDecision, input: EventCaptureInput
) -> UserEventEnvelope:
    symptom_id = _new_id("symptom")
    occurred_at = _now()
    raw = decision.extracted.get("symptom", {})
    data = raw if isinstance(raw, dict) else {}
    severity = {
        "severe": "high",
        "medium": "medium",
        "mild": "low",
        "unknown": "unknown",
    }.get(str(data.get("severity") or "unknown"), "unknown")
    payload = SymptomLoggedPayload(
        symptom_id=symptom_id,
        occurred_at=occurred_at,
        label=str(data.get("category") or data.get("raw_text") or "unknown"),
        severity=severity,
        notes=_note(str(data.get("raw_text") or ""), decision.occurred_at_text),
        safety_checked=True,
    )
    return _envelope(
        input=input,
        event_type="symptom.logged",
        aggregate_type="symptom",
        aggregate_id=symptom_id,
        actor_id="symptom.log",
        payload=payload,
        occurred_at=occurred_at,
    )


def _envelope(
    *,
    input: EventCaptureInput,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    actor_id: str,
    payload: object,
    occurred_at: str,
) -> UserEventEnvelope:
    return UserEventEnvelope(
        event_id=str(uuid4()),
        event_seq=0,
        user_id=input.user_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        occurred_at=occurred_at,
        recorded_at=_now(),
        source="user",
        actor=EventActor(actor_type="tool", actor_id=actor_id),
        idempotency_key=f"{actor_id}:{input.user_id}:{input.normalized_text}",
        payload=payload,
        metadata=EventMetadata(tool_name="event_capture", safety_status="ok"),
    )


def _measurements(data: dict[str, object]) -> list[BiometricMeasurement]:
    unit = str(data.get("unit") or "unknown")
    if data.get("systolic") is not None:
        return [
            BiometricMeasurement(type="other", value=float(data["systolic"]), unit=unit),
            BiometricMeasurement(type="other", value=float(data["diastolic"]), unit=unit),
        ]
    metric = str(data.get("metric") or "other")
    kind = {"weight": "weight", "body_measurement": "waist"}.get(metric, "other")
    value = data.get("value")
    return [
        BiometricMeasurement(
            type=kind,
            value=float(value) if value is not None else 0,
            unit=unit,
        )
    ]


def _numeric_quantity(value: object) -> dict[str, object] | None:
    if not isinstance(value, str):
        return None
    match = re.search(r"\b(\d+(?:[.,]\d+)?)\s*(g|gr|gramos?|ml|tazas?|cucharadas?)\b", value)
    if not match:
        return None
    unit = {
        "gr": "g",
        "gramo": "g",
        "gramos": "g",
        "taza": "cup",
        "tazas": "cup",
        "cucharada": "tbsp",
        "cucharadas": "tbsp",
    }.get(match.group(2), match.group(2))
    return {"value": float(match.group(1).replace(",", ".")), "unit": unit}


def _meal_type(value: object) -> str:
    return str(value) if value in {"breakfast", "lunch", "dinner", "snack", "unknown"} else "unknown"


def _note(reason: str, occurred_at_text: str | None) -> str | None:
    return f"{reason}; occurred_at_text={occurred_at_text}" if occurred_at_text else reason or None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _now() -> str:
    return datetime.now(UTC).isoformat()

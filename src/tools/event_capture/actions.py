from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from domain.events.envelope import EventActor, EventMetadata, UserEventEnvelope
from domain.events.nutrition import MealItem, MealLoggedPayload
from tools.event_capture.contract import EventCaptureDecision


def build_event_capture_event(
    *, decision: EventCaptureDecision, user_id: str, original_text: str
) -> UserEventEnvelope | None:
    if decision.requires_safety_validation:
        return None
    if decision.capture_action != "log_meal":
        return None
    return _build_meal(decision, user_id, original_text)


def _build_meal(
    decision: EventCaptureDecision, user_id: str, original_text: str
) -> UserEventEnvelope:
    meal_id = _new_id("meal")
    occurred_at = _now()
    payload = MealLoggedPayload(
        meal_id=meal_id,
        meal_type="unknown",
        consumed_at=occurred_at,
        source="manual",
        items=[
            MealItem(
                item_id=_new_id("meal_item"),
                food_label=item.name,
                quantity=_quantity(item),
            )
            for item in decision.items
        ],
        notes=_note(decision.reason, decision.occurred_at_text),
    )
    return _envelope(
        user_id=user_id,
        original_text=original_text,
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id=meal_id,
        actor_id="nutrition.log_meal",
        payload=payload,
        occurred_at=occurred_at,
    )


def _envelope(
    *,
    user_id: str,
    original_text: str,
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
        user_id=user_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        occurred_at=occurred_at,
        recorded_at=_now(),
        source="user",
        actor=EventActor(actor_type="tool", actor_id=actor_id),
        idempotency_key=f"{actor_id}:{user_id}:{original_text}",
        payload=payload,
        metadata=EventMetadata(tool_name="event_capture", safety_status="ok"),
    )


def _quantity(item) -> dict[str, object] | None:
    value = item.quantity
    unit = item.unit
    if value is None or unit is None:
        return None
    return {"value": float(value), "unit": unit}


def _note(reason: str, occurred_at_text: str | None) -> str | None:
    return f"{reason}; occurred_at_text={occurred_at_text}" if occurred_at_text else reason or None


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def _now() -> str:
    return datetime.now(UTC).isoformat()

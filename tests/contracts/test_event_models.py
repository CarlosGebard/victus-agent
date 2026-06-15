import pytest
from pydantic import ValidationError

from domain.events.models import (
    EventActor,
    MealLoggedPayload,
    ToolEventRef,
    UserEventEnvelope,
)


def test_meal_logged_payload_validates_nested_items() -> None:
    payload = MealLoggedPayload(
        meal_id="meal-1",
        meal_type="lunch",
        consumed_at="2026-06-12T12:00:00Z",
        source="manual",
        items=[
            {
                "item_id": "item-1",
                "food_label": "pollo",
                "quantity": {"value": 150, "unit": "g"},
            }
        ],
    )

    assert payload.items[0].quantity is not None
    assert payload.items[0].quantity.unit == "g"


def test_event_envelope_requires_schema_version_one() -> None:
    event = UserEventEnvelope(
        event_id="event-1",
        event_seq=1,
        user_id="user-1",
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id="meal-1",
        occurred_at="2026-06-12T12:00:00Z",
        recorded_at="2026-06-12T12:00:01Z",
        source="user",
        actor=EventActor(actor_type="tool", actor_id="nutrition.manage_meal"),
        payload={
            "meal_id": "meal-1",
            "meal_type": "lunch",
            "consumed_at": "2026-06-12T12:00:00Z",
            "source": "manual",
            "items": [],
        },
    )

    assert event.schema_version == 1
    assert event.metadata.trace_id is None


def test_event_models_reject_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ToolEventRef(event_id="event-1", event_type="meal.logged", seq=1, extra=True)

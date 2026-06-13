from events.models import EventActor, MealLoggedPayload, UserEventEnvelope
from events.repository import _event_to_row, _row_to_event


def test_event_row_round_trip() -> None:
    event = UserEventEnvelope(
        event_id="00000000-0000-0000-0000-000000000001",
        event_seq=1,
        user_id="user-1",
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id="meal-1",
        occurred_at="2026-06-12T12:00:00Z",
        recorded_at="2026-06-12T12:00:01Z",
        source="user",
        actor=EventActor(actor_type="tool", actor_id="nutrition.manage_meal"),
        idempotency_key="request-1:meal-1",
        payload=MealLoggedPayload(
            meal_id="meal-1",
            meal_type="lunch",
            consumed_at="2026-06-12T12:00:00Z",
            source="manual",
            items=[],
        ),
    )

    row = _event_to_row(event)
    restored = _row_to_event(row)

    assert row["payload"]["meal_id"] == "meal-1"
    assert restored.event_id == event.event_id
    assert restored.idempotency_key == event.idempotency_key

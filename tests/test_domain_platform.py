from domain.events.envelope import EventActor, UserEventEnvelope
from domain.events.nutrition import MealLoggedPayload
from domain.projections.models import UserProfileProjection
from victus_platform.repositories.events import _event_to_row, _row_to_event
from victus_platform.safety.rules import SafetyPrecheck, SafetyPrecheckInput, evaluate_rules


def test_event_persistence_round_trip_and_projection_defaults() -> None:
    event = UserEventEnvelope(
        event_id="event-1",
        event_seq=1,
        user_id="u1",
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id="meal-1",
        occurred_at="2026-07-18T12:00:00Z",
        recorded_at="2026-07-18T12:00:00Z",
        source="user",
        actor=EventActor(actor_type="tool", actor_id="nutrition.log_meal"),
        idempotency_key="request-1",
        payload=MealLoggedPayload(
            meal_id="meal-1",
            meal_type="lunch",
            consumed_at="2026-07-18T12:00:00Z",
            source="manual",
            items=[],
        ),
    )
    restored = _row_to_event(_event_to_row(event))
    projection = UserProfileProjection(user_id="u1", last_event_seq=0, updated_at="now")
    assert restored.event_id == event.event_id
    assert restored.idempotency_key == event.idempotency_key
    assert restored.payload.meal_id == "meal-1"
    assert projection.restrictions == []


def test_safety_rules_separate_critical_intent_from_harmless_language() -> None:
    result = SafetyPrecheck().check(
        SafetyPrecheckInput(
            original_text="me quiero suicidar",
            working_text="i want to kill myself",
        )
    )
    assert result.decision == "emergency_escalation"
    assert result.audit_required is True
    assert evaluate_rules("this homework is killing me") == []

from __future__ import annotations

from domain.events.envelope import EventActor, EventMetadata, UserEventEnvelope
from domain.events.profile import PreferenceUpdatedPayload
from tools.profile.contract import ProfileUpdateDecision, ProfileUpdateInput
from tools.profile.actions._common import (
    clean_leading_article,
    new_event_id,
    new_prefixed_id,
    now_iso,
)


def build_update_preference_event(
    *,
    decision: ProfileUpdateDecision,
    input: ProfileUpdateInput,
) -> UserEventEnvelope:
    preference_id = new_prefixed_id("preference")
    now = now_iso()
    payload = PreferenceUpdatedPayload(
        preference_id=preference_id,
        category=_contract_category(decision),
        item_label=clean_leading_article(decision.target or decision.category),
        preference=_contract_preference(decision.direction),
        strength=_contract_strength(decision.strength),
        reason=decision.reason,
    )
    return UserEventEnvelope(
        event_id=new_event_id(),
        event_seq=0,
        user_id=input.user_id,
        event_type="preference.updated",
        aggregate_type="preference",
        aggregate_id=preference_id,
        occurred_at=now,
        recorded_at=now,
        source="user",
        actor=EventActor(actor_type="tool", actor_id="profile.update_preference"),
        idempotency_key=(
            f"profile.update_preference:{input.user_id}:{payload.category}:"
            f"{payload.item_label}:{payload.preference}"
        ),
        payload=payload,
        metadata=EventMetadata(tool_name="profile_update", safety_status="ok"),
    )


def _contract_category(decision: ProfileUpdateDecision) -> str:
    if decision.profile_entity_type == "budget_preference":
        return "budget"
    if decision.profile_entity_type == "schedule_preference":
        return "schedule"
    if decision.profile_entity_type == "cooking_preference":
        return "cooking"
    if decision.profile_entity_type == "preference" and decision.direction in {
        "avoid",
        "dislike",
        "include",
        "limit",
        "prefer",
    }:
        return "food"
    if decision.category == "food_dislike":
        return "food"
    if decision.category in {"budget", "schedule", "cooking"}:
        return decision.category
    return "other"


def _contract_preference(direction: str) -> str:
    if direction in {"prefer", "include"}:
        return "like"
    if direction in {"dislike", "avoid", "limit"}:
        return "dislike"
    return "neutral"


def _contract_strength(strength: str) -> float:
    return {
        "hard": 1.0,
        "strong": 0.8,
        "medium": 0.5,
        "weak": 0.25,
        "unknown": 0.5,
    }.get(strength, 0.5)

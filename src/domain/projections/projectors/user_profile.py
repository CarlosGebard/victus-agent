from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from domain.projections.models.user_profile import (
    PreferenceView,
    RestrictionView,
    UserProfileProjection,
)
from domain.projections.projectors._common import now_iso

USER_PROFILE_PROJECTOR = "user_profile"


def apply_user_profile_event(
    projection: UserProfileProjection | None,
    event: UserEventEnvelope,
) -> UserProfileProjection:
    current = projection or UserProfileProjection(
        user_id=event.user_id,
        last_event_seq=0,
        updated_at=now_iso(),
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
    current.updated_at = now_iso()
    return current

from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from tools.profile.contract import ProfileUpdateDecision, ProfileUpdateInput
from tools.profile.actions.add_restriction import build_add_restriction_event
from tools.profile.actions.update_preference import build_update_preference_event


def build_profile_update_event(
    *,
    decision: ProfileUpdateDecision,
    input: ProfileUpdateInput,
) -> UserEventEnvelope | None:
    if decision.profile_action == "add_restriction":
        return build_add_restriction_event(decision=decision, input=input)
    if decision.profile_action == "update_preference":
        return build_update_preference_event(decision=decision, input=input)
    return None

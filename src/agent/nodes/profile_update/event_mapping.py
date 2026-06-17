from __future__ import annotations

from agent.nodes.profile_update.schemas import ProfileUpdateDecision


EVENT_TYPE_BY_ACTION = {
    "add_restriction": "restriction.added",
    "update_restriction": "restriction.updated",
    "remove_restriction": "restriction.removed",
    "update_preference": "preference.updated",
    "remove_preference": "preference.removed",
    "needs_clarification": "none",
    "reroute": "none",
}


def event_type_for_decision(decision: ProfileUpdateDecision) -> str:
    if (
        decision.profile_entity_type == "identity_preference"
        and decision.profile_action == "update_preference"
    ):
        return "profile.identity_updated"
    return EVENT_TYPE_BY_ACTION[decision.profile_action]

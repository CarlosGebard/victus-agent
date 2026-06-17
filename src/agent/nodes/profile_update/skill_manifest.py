from __future__ import annotations


PROFILE_UPDATE_SKILLS = {
    "profile.add_restriction": {
        "emits": ["restriction.added"],
        "allowed_actions": ["add_restriction"],
    },
    "profile.update_restriction": {
        "emits": ["restriction.updated"],
        "allowed_actions": ["update_restriction"],
    },
    "profile.remove_restriction": {
        "emits": ["restriction.removed"],
        "allowed_actions": ["remove_restriction"],
        "requires_confirmation_for": ["allergy", "medical_restriction"],
    },
    "profile.update_preference": {
        "emits": ["preference.updated", "profile.identity_updated"],
        "allowed_actions": ["update_preference"],
    },
    "profile.remove_preference": {
        "emits": ["preference.removed"],
        "allowed_actions": ["remove_preference"],
    },
    "clarification.request": {
        "emits": ["clarification.requested"],
        "allowed_actions": ["needs_clarification"],
    },
    "none": {
        "emits": [],
        "allowed_actions": ["reroute"],
    },
}

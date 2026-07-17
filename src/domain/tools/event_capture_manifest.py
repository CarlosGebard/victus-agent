from __future__ import annotations


EVENT_CAPTURE_SKILLS = {
    "nutrition.log_meal": {
        "emits": ["meal.logged"],
        "allowed_actions": ["log_meal"],
    },
    "nutrition.edit_meal": {
        "emits": ["meal.edited"],
        "allowed_actions": ["edit_meal"],
        "requires_record_reference": True,
    },
    "nutrition.delete_meal": {
        "emits": ["meal.deleted"],
        "allowed_actions": ["delete_meal"],
        "requires_record_reference": True,
        "requires_confirmation": True,
    },
    "biometrics.log": {
        "emits": ["biometrics.logged"],
        "allowed_actions": ["log_biometrics"],
    },
    "lifestyle.log": {
        "emits": ["lifestyle_metric.logged"],
        "allowed_actions": ["log_lifestyle_metric"],
    },
    "symptom.log": {
        "emits": ["symptom.logged"],
        "allowed_actions": ["log_symptom"],
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

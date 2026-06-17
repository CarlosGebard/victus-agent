from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class EventCaptureInput(BaseModel):
    user_id: str
    normalized_text: str
    active_clarification_exists: bool = False
    user_context_digest: str | None = None
    nutrition_status_digest: str | None = None


class EventCaptureDecision(BaseModel):
    capture_action: Literal[
        "log_meal",
        "edit_meal",
        "delete_meal",
        "log_biometrics",
        "log_lifestyle_metric",
        "log_symptom",
        "needs_clarification",
        "reroute",
    ]

    capture_entity_type: Literal[
        "meal",
        "biometrics",
        "lifestyle_metric",
        "symptom",
        "unknown",
    ]

    selected_skill: Literal[
        "nutrition.log_meal",
        "nutrition.edit_meal",
        "nutrition.delete_meal",
        "biometrics.log",
        "lifestyle.log",
        "symptom.log",
        "clarification.request",
        "none",
    ]

    event_type_candidate: Literal[
        "meal.logged",
        "meal.edited",
        "meal.deleted",
        "biometrics.logged",
        "lifestyle_metric.logged",
        "symptom.logged",
        "none",
    ]

    extracted: dict[str, Any] = Field(default_factory=dict)

    referenced_record: str | None = None
    occurred_at_text: str | None = None

    requires_confirmation: bool
    requires_safety_validation: bool

    clarification_question: str | None = None
    reason: str = Field(min_length=1)

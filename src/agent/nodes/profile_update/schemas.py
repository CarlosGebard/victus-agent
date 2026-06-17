from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ProfileUpdateInput(BaseModel):
    user_id: str
    normalized_text: str
    user_context_digest: str | None = None
    constraint_digest: str | None = None


class ProfileUpdateDecision(BaseModel):
    profile_action: Literal[
        "add_restriction",
        "update_restriction",
        "remove_restriction",
        "update_preference",
        "remove_preference",
        "needs_clarification",
        "reroute",
    ]

    profile_entity_type: Literal[
        "restriction",
        "preference",
        "identity_preference",
        "budget_preference",
        "schedule_preference",
        "cooking_preference",
        "unknown",
    ]

    selected_skill: Literal[
        "profile.add_restriction",
        "profile.update_restriction",
        "profile.remove_restriction",
        "profile.update_preference",
        "profile.remove_preference",
        "clarification.request",
        "none",
    ]

    target: str | None = None
    category: str | None = None

    direction: Literal[
        "include",
        "avoid",
        "prefer",
        "dislike",
        "limit",
        "remove",
        "unknown",
    ] = "unknown"

    strength: Literal[
        "hard",
        "strong",
        "medium",
        "weak",
        "unknown",
    ] = "unknown"

    restriction_kind: Literal[
        "allergy",
        "intolerance",
        "medical_restriction",
        "religious_restriction",
        "ethical_restriction",
        "personal_avoidance",
        "not_applicable",
        "unknown",
    ] = "not_applicable"

    severity: Literal[
        "critical",
        "high",
        "medium",
        "low",
        "unknown",
    ] = "unknown"

    requires_confirmation: bool
    requires_safety_validation: bool

    clarification_question: str | None = None

    event_type_candidate: Literal[
        "restriction.added",
        "restriction.updated",
        "restriction.removed",
        "preference.updated",
        "preference.removed",
        "profile.identity_updated",
        "none",
    ] = "none"

    reason: str = Field(min_length=1)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class RecoverProfileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


@dataclass(frozen=True)
class ProfileGatewayResponse:
    status_code: int
    payload: Any = None
    error: str | None = None


class ProfileGateway(Protocol):
    async def fetch(self) -> ProfileGatewayResponse: ...


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

    reason: str = Field(min_length=1)

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from domain.events.base import Severity
from domain.projections.models.base import ContractModel


class HardConstraint(ContractModel):
    constraint_id: str
    kind: Literal["allergy", "medical", "religious", "safety", "system"]
    label: str
    severity: Severity
    rule: dict[str, Any]


class SoftConstraint(ContractModel):
    constraint_id: str
    kind: Literal["preference", "budget", "schedule", "adherence", "cooking"]
    label: str
    strength: float
    rule: dict[str, Any]


class SafetyFlag(ContractModel):
    flag_id: str
    risk_category: str
    status: Literal["warning", "blocked", "needs_clarification"]
    reasons: list[str]


class ConstraintProjection(ContractModel):
    user_id: str
    hard_constraints: list[HardConstraint] = Field(default_factory=list)
    soft_constraints: list[SoftConstraint] = Field(default_factory=list)
    safety_flags: list[SafetyFlag] = Field(default_factory=list)
    derived_from_event_seq: int
    updated_at: str

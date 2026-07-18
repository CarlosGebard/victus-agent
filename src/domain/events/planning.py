from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from domain.events.base import ContractModel


class EnergyTarget(ContractModel):
    type: Literal["delta_daily", "target_daily", "unknown"]
    kcal_per_day: float | None = None


class GoalSetPayload(ContractModel):
    goal_id: str
    primary_goal: Literal["cut", "maintain", "bulk", "performance", "health", "unknown"]
    horizon_weeks: int | None = None
    energy_target: EnergyTarget | None = None
    macro_targets: dict[str, Any] | None = None
    user_confirmed: bool | None = None


class GoalAdjustedPayload(ContractModel):
    goal_id: str
    patch: dict[str, Any]
    reason: str | None = None
    user_confirmed: bool | None = None


class PlanSessionStartedPayload(ContractModel):
    session_id: str
    reason: str
    goal_id: str | None = None
    active_plan_id: str | None = None


class PlanObjective(ContractModel):
    type: str
    direction: str
    priority: int


class PlanRevisionCreatedPayload(ContractModel):
    revision_id: str
    session_id: str
    parent_revision_id: str | None = None
    objectives: list[PlanObjective]
    summary: str | None = None


class PlanArtifactValidation(ContractModel):
    schema_valid: bool
    policy_valid: bool
    safety_status: Literal["ok", "warning", "blocked"]
    warnings: list[str] = Field(default_factory=list)


class PlanArtifactSavedPayload(ContractModel):
    artifact_id: str
    session_id: str
    revision_id: str
    artifact_type: Literal[
        "diet_recommendation",
        "meal_adjustment",
        "weekly_review",
        "general_guidance",
    ]
    artifact: dict[str, Any]
    validation: PlanArtifactValidation


class PlanSessionEndedPayload(ContractModel):
    session_id: str
    status: Literal["completed", "abandoned", "canceled", "error"]
    reason: str | None = None

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from domain.events.base import ContractModel
from domain.events.planning import EnergyTarget, PlanArtifactValidation, PlanObjective

PlanningAction = Literal[
    "set_goal",
    "adjust_goal",
    "start_session",
    "create_revision",
    "save_artifact",
    "end_session",
]


class PlanningInput(ContractModel):
    user_id: str
    action: PlanningAction
    goal_id: str | None = None
    primary_goal: Literal["cut", "maintain", "bulk", "performance", "health", "unknown"] | None = None
    horizon_weeks: int | None = None
    energy_target: EnergyTarget | None = None
    macro_targets: dict[str, Any] | None = None
    patch: dict[str, Any] | None = None
    reason: str | None = None
    session_id: str | None = None
    active_plan_id: str | None = None
    parent_revision_id: str | None = None
    revision_id: str | None = None
    objectives: list[PlanObjective] = Field(default_factory=list)
    summary: str | None = None
    artifact_id: str | None = None
    artifact_type: Literal[
        "diet_recommendation",
        "meal_adjustment",
        "weekly_review",
        "general_guidance",
    ] | None = None
    artifact: dict[str, Any] | None = None
    validation: PlanArtifactValidation | None = None
    status: Literal["completed", "abandoned", "canceled", "error"] | None = None
    user_confirmed: bool | None = None


PlanningDecision = PlanningInput

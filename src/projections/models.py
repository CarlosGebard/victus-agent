from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from events.models import Severity


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RestrictionView(ContractModel):
    restriction_id: str
    kind: str
    label: str
    severity: Severity
    metadata: dict[str, Any] = Field(default_factory=dict)


class PreferenceView(ContractModel):
    preference_id: str
    category: str
    item_label: str
    preference: Literal["like", "neutral", "dislike"]
    strength: float


class UserProfileBody(ContractModel):
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    age_range: str | None = None
    sex_label: str | None = None
    activity_context: str | None = None


class UserProfileProjection(ContractModel):
    user_id: str
    profile: UserProfileBody = Field(default_factory=UserProfileBody)
    restrictions: list[RestrictionView] = Field(default_factory=list)
    preferences: list[PreferenceView] = Field(default_factory=list)
    active_goal_id: str | None = None
    last_event_seq: int
    updated_at: str


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


class RecentMealItem(ContractModel):
    item_id: str
    food_label: str
    quantity: Any | None = None


class RecentMeal(ContractModel):
    meal_id: str
    meal_type: str
    consumed_at: str
    items: list[RecentMealItem]
    status: Literal["active", "deleted"]


class BiometricValue(ContractModel):
    value: float
    unit: str
    measured_at: str


class BiometricSummary(ContractModel):
    latest_weight: BiometricValue | None = None
    latest_height: BiometricValue | None = None
    sleep: Any | None = None
    steps: Any | None = None


class SymptomView(ContractModel):
    symptom_id: str
    label: str
    severity: str | None = None
    occurred_at: str


class ComputedMetrics(ContractModel):
    meal_count_7d: float | None = None
    adherence_rate_7d: float | None = None
    adherence_rate_30d: float | None = None
    weekend_drop_delta: float | None = None
    late_meal_frequency: float | None = None
    consistency_score: float | None = None
    trigger_pattern_score: float | None = None


class NutritionStatusProjection(ContractModel):
    user_id: str
    recent_meals: list[RecentMeal] = Field(default_factory=list)
    biometrics: BiometricSummary = Field(default_factory=BiometricSummary)
    symptoms: list[SymptomView] = Field(default_factory=list)
    computed_metrics: ComputedMetrics = Field(default_factory=ComputedMetrics)
    last_event_seq: int
    updated_at: str


class RevisionSummary(ContractModel):
    revision_id: str
    session_id: str
    created_at: str
    summary: str | None = None


class FeedbackSummary(ContractModel):
    feedback_id: str
    target_type: str
    target_id: str | None = None
    sentiment: str | None = None
    resolved: bool | None = None


class PlanningHistoryProjection(ContractModel):
    user_id: str
    active_session_id: str | None = None
    active_plan_artifact_id: str | None = None
    active_goal_id: str | None = None
    revision_summary: list[RevisionSummary] = Field(default_factory=list)
    feedback_summary: list[FeedbackSummary] = Field(default_factory=list)
    last_event_seq: int
    updated_at: str

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from domain.projections.models.base import ContractModel


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

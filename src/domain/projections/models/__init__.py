from __future__ import annotations

from domain.projections.models.base import ContractModel
from domain.projections.models.constraint import (
    ConstraintProjection,
    HardConstraint,
    SafetyFlag,
    SoftConstraint,
)
from domain.projections.models.nutrition_status import (
    BiometricSummary,
    BiometricValue,
    ComputedMetrics,
    NutritionStatusProjection,
    RecentMeal,
    RecentMealItem,
    SymptomView,
)
from domain.projections.models.planning_history import (
    FeedbackSummary,
    PlanningHistoryProjection,
    RevisionSummary,
)
from domain.projections.models.user_profile import (
    PreferenceView,
    RestrictionView,
    UserProfileBody,
    UserProfileProjection,
)

__all__ = [
    "BiometricSummary",
    "BiometricValue",
    "ComputedMetrics",
    "ConstraintProjection",
    "ContractModel",
    "FeedbackSummary",
    "HardConstraint",
    "NutritionStatusProjection",
    "PlanningHistoryProjection",
    "PreferenceView",
    "RecentMeal",
    "RecentMealItem",
    "RestrictionView",
    "RevisionSummary",
    "SafetyFlag",
    "SoftConstraint",
    "SymptomView",
    "UserProfileBody",
    "UserProfileProjection",
]

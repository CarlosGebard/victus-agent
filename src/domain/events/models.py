from __future__ import annotations

from domain.events.base import (
    ActorType,
    ContractModel,
    EventSource,
    SafetyStatus,
    Severity,
)
from domain.events.envelope import EventActor, EventMetadata, UserEventEnvelope
from domain.events.evidence import ClaimGeneratedPayload, EvidenceCitedPayload
from domain.events.feedback import FeedbackRecordedPayload, FeedbackResolvedPayload
from domain.events.health_metrics import (
    BiometricMeasurement,
    BiometricsLoggedPayload,
    BiometricSource,
    BiometricType,
    LifestyleMetricLoggedPayload,
    SymptomLoggedPayload,
)
from domain.events.interaction import (
    ClarificationRequestedPayload,
    ClarificationResolvedPayload,
    ConfirmationRequestedPayload,
    ConfirmationResolvedPayload,
)
from domain.events.nutrition import (
    MealDeletedPayload,
    MealEditedPayload,
    MealItem,
    MealLoggedPayload,
    MealSource,
    MealType,
    Quantity,
    QuantityUnit,
)
from domain.events.planning import (
    EnergyTarget,
    GoalAdjustedPayload,
    GoalSetPayload,
    PlanArtifactSavedPayload,
    PlanArtifactValidation,
    PlanObjective,
    PlanRevisionCreatedPayload,
    PlanSessionEndedPayload,
    PlanSessionStartedPayload,
)
from domain.events.profile import (
    PreferenceUpdatedPayload,
    RestrictionAddedPayload,
    RestrictionUpdatedPayload,
)
from domain.events.refs import ToolEventRef
from domain.events.registry import DomainEventPayload
from domain.events.safety import SafetyActionBlockedPayload, SafetyGuardTriggeredPayload

__all__ = [
    "ActorType",
    "BiometricMeasurement",
    "BiometricSource",
    "BiometricType",
    "BiometricsLoggedPayload",
    "ClaimGeneratedPayload",
    "ClarificationRequestedPayload",
    "ClarificationResolvedPayload",
    "ConfirmationRequestedPayload",
    "ConfirmationResolvedPayload",
    "ContractModel",
    "DomainEventPayload",
    "EnergyTarget",
    "EventActor",
    "EventMetadata",
    "EventSource",
    "EvidenceCitedPayload",
    "FeedbackRecordedPayload",
    "FeedbackResolvedPayload",
    "GoalAdjustedPayload",
    "GoalSetPayload",
    "LifestyleMetricLoggedPayload",
    "MealDeletedPayload",
    "MealEditedPayload",
    "MealItem",
    "MealLoggedPayload",
    "MealSource",
    "MealType",
    "PlanArtifactSavedPayload",
    "PlanArtifactValidation",
    "PlanObjective",
    "PlanRevisionCreatedPayload",
    "PlanSessionEndedPayload",
    "PlanSessionStartedPayload",
    "PreferenceUpdatedPayload",
    "Quantity",
    "QuantityUnit",
    "RestrictionAddedPayload",
    "RestrictionUpdatedPayload",
    "SafetyActionBlockedPayload",
    "SafetyGuardTriggeredPayload",
    "SafetyStatus",
    "Severity",
    "SymptomLoggedPayload",
    "ToolEventRef",
    "UserEventEnvelope",
]

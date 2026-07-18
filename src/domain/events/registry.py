from __future__ import annotations

from domain.events.evidence import ClaimGeneratedPayload, EvidenceCitedPayload
from domain.events.feedback import FeedbackRecordedPayload, FeedbackResolvedPayload
from domain.events.health_metrics import (
    BiometricsLoggedPayload,
    LifestyleMetricLoggedPayload,
    SymptomLoggedPayload,
)
from domain.events.interaction import (
    ClarificationRequestedPayload,
    ClarificationResolvedPayload,
    ConfirmationRequestedPayload,
    ConfirmationResolvedPayload,
)
from domain.events.nutrition import MealDeletedPayload, MealEditedPayload, MealLoggedPayload
from domain.events.planning import (
    GoalAdjustedPayload,
    GoalSetPayload,
    PlanArtifactSavedPayload,
    PlanRevisionCreatedPayload,
    PlanSessionEndedPayload,
    PlanSessionStartedPayload,
)
from domain.events.profile import (
    PreferenceUpdatedPayload,
    RestrictionAddedPayload,
    RestrictionUpdatedPayload,
)
from domain.events.safety import SafetyActionBlockedPayload, SafetyGuardTriggeredPayload

DomainEventPayload = (
    MealLoggedPayload
    | MealEditedPayload
    | MealDeletedPayload
    | BiometricsLoggedPayload
    | LifestyleMetricLoggedPayload
    | SymptomLoggedPayload
    | RestrictionAddedPayload
    | RestrictionUpdatedPayload
    | PreferenceUpdatedPayload
    | GoalSetPayload
    | GoalAdjustedPayload
    | PlanSessionStartedPayload
    | PlanRevisionCreatedPayload
    | PlanArtifactSavedPayload
    | PlanSessionEndedPayload
    | FeedbackRecordedPayload
    | FeedbackResolvedPayload
    | ClarificationRequestedPayload
    | ClarificationResolvedPayload
    | ConfirmationRequestedPayload
    | ConfirmationResolvedPayload
    | SafetyGuardTriggeredPayload
    | SafetyActionBlockedPayload
    | ClaimGeneratedPayload
    | EvidenceCitedPayload
)

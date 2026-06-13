from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SafetyStatus = Literal["ok", "warning", "blocked", "needs_clarification"]

EventSource = Literal["user", "system", "import", "migration", "test"]
ActorType = Literal["user", "assistant", "system", "tool"]
MealType = Literal["breakfast", "lunch", "dinner", "snack", "unknown"]
MealSource = Literal["manual", "voice", "import"]
QuantityUnit = Literal["g", "ml", "unit", "serving", "cup", "tbsp", "tsp", "unknown"]
BiometricType = Literal["weight", "height", "sleep", "steps", "body_fat", "waist", "other"]
BiometricSource = Literal["manual", "wearable", "import"]
Severity = Literal["low", "medium", "high", "unknown"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Quantity(ContractModel):
    value: float
    unit: QuantityUnit


class MealItem(ContractModel):
    item_id: str
    food_label: str
    quantity: Quantity | None = None
    notes: str | None = None


class MealLoggedPayload(ContractModel):
    meal_id: str
    meal_type: MealType
    consumed_at: str
    source: MealSource
    items: list[MealItem]
    notes: str | None = None


class MealEditedPayload(ContractModel):
    meal_id: str
    reason: str | None = None
    patch: dict[str, Any]


class MealDeletedPayload(ContractModel):
    meal_id: str
    reason: str | None = None
    user_confirmed: Literal[True]


class BiometricMeasurement(ContractModel):
    type: BiometricType
    value: float
    unit: str


class BiometricsLoggedPayload(ContractModel):
    measurement_id: str
    measured_at: str
    measurements: list[BiometricMeasurement]
    source: BiometricSource


class SymptomLoggedPayload(ContractModel):
    symptom_id: str
    occurred_at: str
    label: str
    severity: Severity | None = None
    duration: str | None = None
    notes: str | None = None
    safety_checked: bool


class RestrictionAddedPayload(ContractModel):
    restriction_id: str
    restriction_kind: Literal["medical", "religious", "allergy", "intolerance", "advisory", "unknown"]
    condition_label: str | None = None
    restricted_substance_label: str
    severity: Severity
    scope: Literal["absolute", "dietary", "advisory", "unknown"]
    evidence_level: Literal["declared", "clinical", "unknown"]


class RestrictionUpdatedPayload(ContractModel):
    restriction_id: str
    patch: dict[str, Any]
    reason: str | None = None


class PreferenceUpdatedPayload(ContractModel):
    preference_id: str
    category: Literal["food", "cuisine", "budget", "time", "schedule", "cooking", "other"]
    item_label: str
    preference: Literal["like", "neutral", "dislike"]
    strength: float
    reason: str | None = None


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


class FeedbackRecordedPayload(ContractModel):
    feedback_id: str
    target_type: Literal["plan", "meal", "recommendation", "answer", "other"]
    target_id: str | None = None
    sentiment: Literal["positive", "neutral", "negative", "mixed"] | None = None
    text: str


class FeedbackResolvedPayload(ContractModel):
    feedback_id: str
    resolution: Literal["accepted", "rejected", "incorporated", "needs_more_info"]
    linked_revision_id: str | None = None


class ClarificationRequestedPayload(ContractModel):
    clarification_id: str
    blocked_node: str | None = None
    blocked_action: str | None = None
    missing_fields: list[str]
    question: str
    expected_answer_type: str


class ClarificationResolvedPayload(ContractModel):
    clarification_id: str
    answer: str
    resume_node: str | None = None
    resume_action: str | None = None


class SafetyGuardTriggeredPayload(ContractModel):
    risk_category: str
    safety_status: Literal["warning", "blocked", "needs_clarification"]
    reasons: list[str]
    checked_action: dict[str, Any] | None = None


class SafetyActionBlockedPayload(ContractModel):
    risk_category: str
    reasons: list[str]
    blocked_action: dict[str, Any]


class ClaimGeneratedPayload(ContractModel):
    claim_id: str
    text: str
    claim_type: Literal["plan_rationale", "evidence_answer", "safety_explanation", "general"]
    grounded: bool


class EvidenceCitedPayload(ContractModel):
    citation_id: str
    claim_id: str | None = None
    evidence_id: str
    source_type: Literal["paper", "guideline", "curated_note", "external"]
    citation_text: str | None = None
    relevance_score: float | None = None


DomainEventPayload = (
    MealLoggedPayload
    | MealEditedPayload
    | MealDeletedPayload
    | BiometricsLoggedPayload
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
    | SafetyGuardTriggeredPayload
    | SafetyActionBlockedPayload
    | ClaimGeneratedPayload
    | EvidenceCitedPayload
)


class EventActor(ContractModel):
    actor_type: ActorType
    actor_id: str | None = None


class EventMetadata(ContractModel):
    node_id: str | None = None
    tool_name: str | None = None
    confidence: float | None = None
    safety_status: SafetyStatus | None = None
    trace_id: str | None = None
    request_id: str | None = None


class UserEventEnvelope(ContractModel):
    event_id: str
    event_seq: int
    user_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    occurred_at: str
    recorded_at: str
    source: EventSource
    actor: EventActor
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    schema_version: Literal[1] = 1
    payload: DomainEventPayload | dict[str, Any]
    metadata: EventMetadata = Field(default_factory=EventMetadata)


class ToolEventRef(ContractModel):
    event_id: str
    event_type: str
    seq: int

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

IntentType = Literal[
    "log_update_data",
    "new_plan",
    "revise_plan",
    "weekly_review",
    "evidence_question",
    "profile_update",
    "risk_medical_unsafe",
    "mixed_ambiguous",
]

RouteName = Literal[
    "EventCaptureGraph",
    "PlanningSessionGraph",
    "PlanRevisionGraph",
    "WeeklyReviewGraph",
    "EvidenceAnswerGraph",
    "ProfileUpdateGraph",
    "SafetyTriageRoute",
    "MixedIntentResolver",
    "ClarificationRoute",
]

DecisionType = Literal[
    "route",
    "clarify",
    "mixed",
    "safety",
]

SafetySeverity = Literal["none", "medium", "high", "urgent"]


class IntentScore(BaseModel):
    intent_type: IntentType
    route: RouteName
    score: float
    positive_score: float
    definition_score: float
    boundary_score: float
    negative_score: float
    matched_signals: list[str] = Field(default_factory=list)


class RouteDecision(BaseModel):
    router_version: str
    input_text: str
    normalized_text: str

    decision: DecisionType
    route: RouteName

    intent_type: IntentType | None = None
    secondary_intents: list[IntentType] = Field(default_factory=list)

    confidence: float
    margin: float | None = None

    requires_clarification: bool = False
    clarification_question: str | None = None

    requires_safety_overlay: bool = False
    safety_reason: str | None = None

    scores: list[IntentScore] = Field(default_factory=list)


class SafetyGateResult(BaseModel):
    triggered: bool
    reason: str | None = None
    severity: SafetySeverity = "none"

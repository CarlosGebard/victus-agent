from __future__ import annotations

from typing import Any, Literal, TypedDict

from events.models import ToolEventRef
from projections.models import (
    ConstraintProjection,
    NutritionStatusProjection,
    PlanningHistoryProjection,
    UserProfileProjection,
)
from tools.models import ToolResult


class RequestState(TypedDict, total=False):
    request_id: str
    user_id: str
    raw_text: str
    normalized_text: str
    received_at: str
    locale: str
    timezone: str


class SafetyState(TypedDict):
    status: Literal["unknown", "ok", "warning", "blocked", "needs_clarification"]
    reasons: list[str]


class IntentState(TypedDict, total=False):
    primary_intent: str
    confidence: float
    rationale: str
    target_node: str
    subintents: list[str]


class ProjectionState(TypedDict, total=False):
    user_profile: UserProfileProjection
    constraint: ConstraintProjection
    nutrition_status: NutritionStatusProjection
    planning_history: PlanningHistoryProjection
    loaded_at: str
    max_event_seq: int


class ToolContextState(TypedDict, total=False):
    allowed_tools: list[str]
    proposed_action: dict[str, Any]
    last_tool_result: ToolResult
    tool_results: list[ToolResult]


class PlanningState(TypedDict, total=False):
    session_id: str
    revision_id: str
    artifact_id: str
    candidate_artifact: dict[str, Any]
    validation_report: dict[str, Any]


class EvidenceState(TypedDict, total=False):
    query: str
    retrieved_evidence: list[Any]
    cited_evidence: list[Any]
    generated_claims: list[Any]


class ClarificationState(TypedDict, total=False):
    clarification_id: str
    missing_fields: list[str]
    question: str
    expected_answer_type: str
    resume_node: str
    resume_action: str


class ResponseState(TypedDict, total=False):
    mode: Literal["final", "clarification", "blocked", "error"]
    user_message: str
    internal_notes: list[str]


class AuditState(TypedDict):
    node_path: list[str]
    events_emitted: list[ToolEventRef]
    warnings: list[str]
    errors: list[str]


class VictusGraphState(TypedDict, total=False):
    request: RequestState
    safety: SafetyState
    intent: IntentState
    projections: ProjectionState
    tool_context: ToolContextState
    planning: PlanningState
    evidence: EvidenceState
    clarification: ClarificationState
    response: ResponseState
    audit: AuditState

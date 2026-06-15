from __future__ import annotations

from typing import Any, Literal, TypedDict

from domain.events.models import ToolEventRef
from domain.projections.models import (
    ConstraintProjection,
    NutritionStatusProjection,
    PlanningHistoryProjection,
    UserProfileProjection,
)
from domain.tools.models import ToolResult
from domain.session_context.models import BootstrapContext, ConversationStateSummary, PendingInteractionState


class RequestState(TypedDict, total=False):
    request_id: str
    user_id: str
    raw_text: str
    normalized_text: str
    received_at: str
    locale: str
    timezone: str
    conversation_id: str
    routing_query: str


class SessionContextState(TypedDict, total=False):
    conversation_id: str
    summary: ConversationStateSummary
    pending_interaction: PendingInteractionState
    bootstrap: BootstrapContext
    updated_summary: ConversationStateSummary


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
    session_context: SessionContextState
    safety: SafetyState
    intent: IntentState
    projections: ProjectionState
    tool_context: ToolContextState
    planning: PlanningState
    evidence: EvidenceState
    clarification: ClarificationState
    response: ResponseState
    audit: AuditState

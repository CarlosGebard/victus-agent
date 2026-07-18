from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from tools.contracts import ToolExecution, ToolExposure, ToolResult
from tools.event_capture.contract import EventCaptureInput
from tools.event_capture.tool import execute as execute_event_capture
from tools.evidence.contract import EvidenceAnswerInput
from tools.evidence.tool import execute as execute_evidence
from tools.feedback.contract import FeedbackInput
from tools.feedback.tool import execute as execute_feedback
from tools.interaction.clarification import execute as execute_clarification
from tools.interaction.confirmation import execute as execute_confirmation
from tools.interaction.contract import ClarificationInput, ConfirmationInput
from tools.planning.contract import PlanningInput
from tools.planning.tool import execute as execute_planning
from tools.profile.contract import ProfileUpdateInput
from tools.profile.contract import RecoverProfileInput
from tools.profile.remote import execute as execute_remote_profile
from tools.profile.tool import execute as execute_profile

ToolImplementation = Callable[..., ToolExecution | Any]
ALL_EXPOSURES = frozenset({"langgraph", "mcp", "cli", "test"})


def _description(name: str) -> str:
    return {
        "event_capture": (
            "Use when the user reports a concrete event that happened or is happening: a meal, "
            "biometric measurement, symptom, or lifestyle metric such as sleep or exercise. "
            "Capture the user's original meaning in normalized_text. Do not use for durable "
            "preferences or restrictions, future goals or plans, feedback, or profile reads."
        ),
        "profile_update": (
            "Use when the user asks to add, change, or remove durable profile information such as "
            "an allergy, intolerance, dietary restriction, food preference, budget preference, "
            "schedule preference, or cooking preference. Do not use for a meal or symptom that "
            "occurred once, a future goal, feedback about a result, or reading the current profile."
        ),
        "planning": (
            "Use for explicit planning lifecycle operations: set or adjust a health, weight, or "
            "performance goal; start or end a planning session; create a plan revision; or save a "
            "validated planning artifact. Do not use to log past meals or measurements, update "
            "durable restrictions or preferences, or record the user's opinion about a plan."
        ),
        "feedback": (
            "Use when the user evaluates or reacts to a specific plan, meal, recommendation, or "
            "answer, or when recorded feedback must be resolved. Record the target and sentiment "
            "when known. Do not use to revise the plan directly, capture a health event, or update "
            "a durable profile preference unless a separate workflow explicitly does so."
        ),
        "evidence_answer": (
            "Use to persist an already produced grounded claim or attach a citation to a claim, "
            "including plan rationale, evidence answers, and safety explanations. Do not use to "
            "search for sources, fabricate evidence, answer an ungrounded question, capture user "
            "events, or update the user's profile or plan."
        ),
        "clarification": (
            "Continuation mechanism for a workflow that cannot proceed because required information "
            "is missing. Use action=request to record the missing fields and question, or "
            "action=resolve to record the user's answer and resume the blocked workflow. Do not use "
            "for general questions or when the intended action already has enough information."
        ),
        "confirmation": (
            "Continuation mechanism for an identified action that requires explicit user approval "
            "before execution. Use action=request to ask for approval, or action=resolve to record "
            "the answer and resume the blocked action. Do not use without a specific pending action "
            "and do not treat ordinary agreement or conversational yes/no answers as confirmation."
        ),
        "recuperar_perfil": (
            "Use when the authenticated user asks to view or retrieve their current Victus profile "
            "from the backend, including stored goals, restrictions, and preferences. This is a "
            "read-only tool and takes no arguments. Do not use to modify the profile, infer a user "
            "identity, or retrieve another user's profile."
        ),
    }[name]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    version: str
    description: str
    category: str
    risk: str
    side_effects: bool
    requires_identity: bool
    exposures: frozenset[ToolExposure]
    input_model: type[BaseModel]
    output_model: type[BaseModel]
    implementation: ToolImplementation

    @property
    def input_schema(self) -> dict[str, Any]:
        return self.input_model.model_json_schema()


_DEFINITIONS = (
    ("event_capture", EventCaptureInput, execute_event_capture, "capture", "high", True),
    ("profile_update", ProfileUpdateInput, execute_profile, "profile", "high", True),
    ("planning", PlanningInput, execute_planning, "planning", "medium", True),
    ("feedback", FeedbackInput, execute_feedback, "feedback", "low", True),
    ("evidence_answer", EvidenceAnswerInput, execute_evidence, "evidence", "medium", True),
    ("clarification", ClarificationInput, execute_clarification, "interaction", "low", True),
    ("confirmation", ConfirmationInput, execute_confirmation, "interaction", "medium", True),
    ("recuperar_perfil", RecoverProfileInput, execute_remote_profile, "profile", "low", False),
)

TOOL_DEFINITIONS = {
    name: ToolDefinition(
        name=name,
        version="1",
        description=_description(name),
        category=category,
        risk=risk,
        side_effects=side_effects,
        requires_identity=name == "recuperar_perfil",
        exposures=ALL_EXPOSURES,
        input_model=input_model,
        output_model=ToolResult,
        implementation=implementation,
    )
    for name, input_model, implementation, category, risk, side_effects in _DEFINITIONS
}


def list_tools(*, exposure: ToolExposure | None = None) -> list[ToolDefinition]:
    definitions = list(TOOL_DEFINITIONS.values())
    return [item for item in definitions if exposure is None or exposure in item.exposures]


def get_tool(name: str) -> ToolDefinition:
    try:
        return TOOL_DEFINITIONS[name]
    except KeyError as exc:
        raise ValueError(f"unknown tool: {name}") from exc

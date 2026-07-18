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
        "event_capture": "Capture meals, biometrics, symptoms, and lifestyle metrics.",
        "profile_update": "Update durable user restrictions and preferences.",
        "planning": "Record goals, planning sessions, revisions, and artifacts.",
        "feedback": "Record or resolve user feedback.",
        "evidence_answer": "Record grounded claims and citations.",
        "clarification": "Request or resolve missing information.",
        "confirmation": "Request or resolve confirmation for sensitive changes.",
        "recuperar_perfil": "Recover the authenticated user's Victus profile.",
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

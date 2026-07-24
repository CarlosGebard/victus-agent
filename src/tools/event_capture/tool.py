from __future__ import annotations

from tools.contracts import (
    ClarificationRequest,
    ToolContext,
    ToolExecution,
    ToolResult,
    ToolServices,
)
from tools.event_capture.actions import build_event_capture_event
from tools.event_capture.contract import EventCaptureInput
from tools.event_capture.policy import decide_with_policy, validate_decision


def execute(
    input_data: EventCaptureInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    original_text = context.original_text or ", ".join(item.name for item in input_data.items)
    decision = validate_decision(
        decide_with_policy(input_data, original_text=original_text),
        input_data,
    )
    if decision.capture_action == "needs_clarification":
        status = "needs_clarification"
    else:
        status = "success"
    user_id = context.identity.subject
    if not user_id:
        raise ValueError("event_capture requires an authenticated user")
    event = build_event_capture_event(
        decision=decision,
        user_id=user_id,
        original_text=original_text,
    )
    return ToolExecution(
        result=ToolResult(
            status=status,
            data=_result_data(decision),
            clarification=_clarification_request(decision) if status == "needs_clarification" else None,
        ),
        events=(event,) if event is not None and status == "success" else (),
    )


def _result_data(decision) -> dict[str, object]:
    if decision.capture_action == "needs_clarification":
        return {
            "capture_action": decision.capture_action,
            "missing_fields": decision.missing_fields,
        }
    return {
        "capture_action": decision.capture_action,
        "items": [item.model_dump(mode="json") for item in decision.items],
        "occurred_at_text": decision.occurred_at_text,
    }


def _clarification_request(decision) -> ClarificationRequest:
    missing = decision.missing_fields
    if not isinstance(missing, list) or not all(isinstance(item, str) for item in missing):
        missing = ["event_details"]
    return ClarificationRequest(
        missing_fields=missing,
        question=decision.clarification_question or "Necesito mas informacion.",
        expected_answer_type="free_text",
        resume_node="agent_decision",
        resume_action="event_capture",
    )

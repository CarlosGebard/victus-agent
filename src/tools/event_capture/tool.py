from __future__ import annotations

from tools.contracts import ToolContext, ToolExecution, ToolMeta, ToolResult, ToolServices
from tools.event_capture.actions import build_event_capture_event
from tools.event_capture.contract import EventCaptureInput
from tools.event_capture.policy import decide_with_policy, validate_decision


def execute(
    input_data: EventCaptureInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    decision = validate_decision(decide_with_policy(input_data), input_data)
    if decision.requires_safety_validation:
        status = "blocked"
    elif decision.capture_action == "needs_clarification":
        status = "needs_clarification"
    elif decision.capture_action == "reroute":
        status = "rejected"
    else:
        status = "success"
    event = build_event_capture_event(decision=decision, input=input_data)
    return ToolExecution(
        result=ToolResult(
            status=status,
            data=decision.model_dump(mode="json"),
            meta=ToolMeta(handler_version="event_capture.v1", trace_id=context.trace_id),
        ),
        events=(event,) if event is not None and status == "success" else (),
    )

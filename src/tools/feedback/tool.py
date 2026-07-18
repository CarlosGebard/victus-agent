from __future__ import annotations

from tools.contracts import ToolContext, ToolExecution, ToolMeta, ToolResult, ToolServices
from tools.feedback.actions import build_feedback_event
from tools.feedback.contract import FeedbackInput
from tools.feedback.policy import decide_with_policy


def execute(
    input_data: FeedbackInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    decision = decide_with_policy(input_data)
    event = build_feedback_event(decision=decision, input=input_data)
    return ToolExecution(
        result=ToolResult(
            status="success",
            data=decision.model_dump(mode="json"),
            meta=ToolMeta(handler_version="feedback.v1", trace_id=context.trace_id),
        ),
        events=(event,) if event is not None else (),
    )

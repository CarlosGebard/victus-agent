from __future__ import annotations

from domain.events.interaction import ClarificationRequestedPayload, ClarificationResolvedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.contracts import ToolContext, ToolExecution, ToolMeta, ToolResult, ToolServices
from tools.interaction.contract import ClarificationInput


def execute(
    input_data: ClarificationInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    _validate(input_data)
    event = _build_event(input_data)
    return ToolExecution(
        result=ToolResult(
            status="needs_clarification" if input_data.action == "request" else "success",
            data=input_data.model_dump(mode="json"),
            meta=ToolMeta(handler_version="clarification.v1", trace_id=context.trace_id),
        ),
        events=(event,),
    )


def _validate(value: ClarificationInput) -> None:
    if value.action == "request" and (not value.question or not value.missing_fields):
        raise ValueError("clarification request requires question and missing_fields")
    if value.action == "resolve" and (not value.clarification_id or not value.answer):
        raise ValueError("clarification resolve requires clarification_id and answer")


def _build_event(value: ClarificationInput):
    clarification_id = value.clarification_id or new_prefixed_id("clarification")
    if value.action == "request":
        payload = ClarificationRequestedPayload(
            clarification_id=clarification_id,
            blocked_node=value.blocked_node,
            blocked_action=value.blocked_action,
            missing_fields=value.missing_fields,
            question=value.question or "",
            expected_answer_type=value.expected_answer_type or "free_text",
        )
        event_type, safety = "clarification.requested", "needs_clarification"
    else:
        payload = ClarificationResolvedPayload(
            clarification_id=clarification_id,
            answer=value.answer or "",
            resume_node=value.resume_node,
            resume_action=value.resume_action,
        )
        event_type, safety = "clarification.resolved", "ok"
    return tool_event_envelope(
        user_id=value.user_id,
        tool_name="clarification",
        event_type=event_type,
        aggregate_type="interaction",
        aggregate_id=clarification_id,
        actor_id=f"clarification.{value.action}",
        payload=payload,
        idempotency_key=f"clarification:{value.action}:{value.user_id}:{clarification_id}",
        safety_status=safety,
    )

from __future__ import annotations

from domain.events.interaction import ConfirmationRequestedPayload, ConfirmationResolvedPayload
from tools._event_builder import new_prefixed_id, tool_event_envelope
from tools.contracts import ToolContext, ToolExecution, ToolMeta, ToolResult, ToolServices
from tools.interaction.contract import ConfirmationInput


def execute(
    input_data: ConfirmationInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    _validate(input_data)
    event = _build_event(input_data)
    return ToolExecution(
        result=ToolResult(
            status="needs_clarification" if input_data.action == "request" else "success",
            data=input_data.model_dump(mode="json"),
            meta=ToolMeta(handler_version="confirmation.v1", trace_id=context.trace_id),
        ),
        events=(event,),
    )


def _validate(value: ConfirmationInput) -> None:
    if value.action == "request" and not value.question:
        raise ValueError("confirmation request requires question")
    if value.action == "resolve" and (
        not value.confirmation_id or value.accepted is None
    ):
        raise ValueError("confirmation resolve requires confirmation_id and accepted")


def _build_event(value: ConfirmationInput):
    confirmation_id = value.confirmation_id or new_prefixed_id("confirmation")
    if value.action == "request":
        payload = ConfirmationRequestedPayload(
            confirmation_id=confirmation_id,
            blocked_node=value.blocked_node,
            blocked_action=value.blocked_action,
            question=value.question or "",
            risk_level=value.risk_level or "medium",
        )
        event_type, safety = "confirmation.requested", "needs_clarification"
    else:
        payload = ConfirmationResolvedPayload(
            confirmation_id=confirmation_id,
            accepted=bool(value.accepted),
            answer=value.answer,
            resume_node=value.resume_node,
            resume_action=value.resume_action,
        )
        event_type, safety = "confirmation.resolved", "ok"
    return tool_event_envelope(
        user_id=value.user_id,
        tool_name="confirmation",
        event_type=event_type,
        aggregate_type="interaction",
        aggregate_id=confirmation_id,
        actor_id=f"confirmation.{value.action}",
        payload=payload,
        idempotency_key=f"confirmation:{value.action}:{value.user_id}:{confirmation_id}",
        safety_status=safety,
    )

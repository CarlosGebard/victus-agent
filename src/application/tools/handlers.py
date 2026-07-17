from __future__ import annotations

from typing import Any

from application.tools.remote_profile import recuperar_perfil
from domain.tools.models import ToolMeta, ToolResult
from domain.tools.event_capture import EventCaptureInput
from domain.tools.event_capture_policy import decide_with_policy as decide_event_capture
from domain.tools.event_capture_validators import validate_event_capture_decision
from domain.tools.profile_update import ProfileUpdateInput
from domain.tools.profile_update_policy import decide_with_policy as decide_profile_update
from domain.tools.profile_update_validators import validate_profile_update_decision


class ToolExecutionError(ValueError):
    pass


def execute_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    if name == "event_capture":
        input_data = EventCaptureInput.model_validate(arguments)
        decision = validate_event_capture_decision(decide_event_capture(input_data), input_data)
        return ToolResult(
            status=_status_from_decision(
                action=decision.capture_action,
                requires_safety_validation=decision.requires_safety_validation,
            ),
            data=decision.model_dump(mode="json"),
            meta=ToolMeta(handler_version="event_capture.v1"),
        )

    if name == "profile_update":
        input_data = ProfileUpdateInput.model_validate(arguments)
        decision = validate_profile_update_decision(decide_profile_update(input_data), input_data)
        return ToolResult(
            status=_status_from_decision(
                action=decision.profile_action,
                requires_safety_validation=decision.requires_safety_validation,
            ),
            data=decision.model_dump(mode="json"),
            meta=ToolMeta(handler_version="profile_update.v1"),
        )

    raise ToolExecutionError(f"unknown tool: {name}")


async def execute_tool_async(name: str, arguments: dict[str, Any]) -> ToolResult:
    if name == "recuperar_perfil":
        if arguments:
            from domain.tools.profile_remote import RecoverProfileInput

            RecoverProfileInput.model_validate(arguments)
        return await recuperar_perfil()
    return execute_tool(name, arguments)


def _status_from_decision(*, action: str, requires_safety_validation: bool) -> str:
    if action == "needs_clarification":
        return "needs_clarification"
    if action == "reroute":
        return "rejected"
    if requires_safety_validation:
        return "blocked"
    return "success"

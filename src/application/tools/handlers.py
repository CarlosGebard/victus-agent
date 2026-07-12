from __future__ import annotations

from typing import Any

from agent.nodes.event_capture import EventCaptureInput, event_capture_node
from agent.nodes.profile_update import ProfileUpdateInput, profile_update_node
from domain.tools.models import ToolMeta, ToolResult


class ToolExecutionError(ValueError):
    pass


def execute_tool(name: str, arguments: dict[str, Any]) -> ToolResult:
    if name == "event_capture":
        input_data = EventCaptureInput.model_validate(arguments)
        decision = event_capture_node().run(input_data)
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
        decision = profile_update_node().run(input_data)
        return ToolResult(
            status=_status_from_decision(
                action=decision.profile_action,
                requires_safety_validation=decision.requires_safety_validation,
            ),
            data=decision.model_dump(mode="json"),
            meta=ToolMeta(handler_version="profile_update.v1"),
        )

    raise ToolExecutionError(f"unknown tool: {name}")


def _status_from_decision(*, action: str, requires_safety_validation: bool) -> str:
    if action == "needs_clarification":
        return "needs_clarification"
    if action == "reroute":
        return "rejected"
    if requires_safety_validation:
        return "blocked"
    return "success"

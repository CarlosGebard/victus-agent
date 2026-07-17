from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from domain.tools.event_capture import EventCaptureInput
from domain.tools.profile_update import ProfileUpdateInput
from domain.tools.models import ToolResult
from domain.tools.profile_remote import RecoverProfileInput

ToolHandler = Callable[[dict[str, Any]], ToolResult]


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_model: type
    visible_to_model: bool
    writes_events: bool

    @property
    def input_schema(self) -> dict[str, Any]:
        return self.input_model.model_json_schema()


TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    "event_capture": ToolDefinition(
        name="event_capture",
        description="Classify fast-changing user data such as meals, biometrics, symptoms, and lifestyle metrics.",
        input_model=EventCaptureInput,
        visible_to_model=True,
        writes_events=False,
    ),
    "profile_update": ToolDefinition(
        name="profile_update",
        description="Classify durable user profile changes such as restrictions, preferences, and schedule context.",
        input_model=ProfileUpdateInput,
        visible_to_model=True,
        writes_events=False,
    ),
    "recuperar_perfil": ToolDefinition(
        name="recuperar_perfil",
        description="Recover the authenticated user's Victus profile from the web backend.",
        input_model=RecoverProfileInput,
        visible_to_model=True,
        writes_events=False,
    ),
}


def list_tools(*, visible_only: bool = False) -> list[ToolDefinition]:
    tools = list(TOOL_DEFINITIONS.values())
    if visible_only:
        return [tool for tool in tools if tool.visible_to_model]
    return tools


def get_tool(name: str) -> ToolDefinition:
    try:
        return TOOL_DEFINITIONS[name]
    except KeyError as exc:
        raise KeyError(f"unknown tool: {name}") from exc

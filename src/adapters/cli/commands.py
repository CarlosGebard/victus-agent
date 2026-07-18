from __future__ import annotations

from typing import Any

from bootstrap.runtime import build_runtime
from victus_platform.identity.local_session import get_local_token
from tools.catalog import get_tool, list_tools
from tools.contracts import ToolContext, ToolIdentity, ToolInvocation


def list_tool_data() -> list[dict[str, Any]]:
    return [_definition_data(item) for item in list_tools(exposure="cli")]


def inspect_tool(name: str) -> dict[str, Any]:
    return _definition_data(get_tool(name), include_schema=True)


async def invoke_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    token = get_local_token()
    result = await build_runtime().invoke_async(
        ToolInvocation(
            name=name,
            arguments=arguments,
            context=ToolContext(
                source="cli",
                identity=ToolIdentity(authenticated=bool(token)),
            ),
        )
    )
    return result.model_dump(mode="json")


def _definition_data(definition, *, include_schema: bool = False) -> dict[str, Any]:
    data = {
        "name": definition.name,
        "version": definition.version,
        "description": definition.description,
        "category": definition.category,
        "risk": definition.risk,
        "side_effects": definition.side_effects,
    }
    if include_schema:
        data["input_schema"] = definition.input_schema
    return data

from __future__ import annotations

from typing import Any, cast

from tools.contracts import (
    ToolContext,
    ToolExecution,
    ToolMeta,
    ToolResult,
    ToolServices,
    ToolStatus,
)
from tools.profile.contract import ProfileGateway, RecoverProfileInput


async def execute(
    input_data: RecoverProfileInput, context: ToolContext, services: ToolServices
) -> ToolExecution:
    gateway = cast(ProfileGateway, services.require("profile_gateway"))
    response = await gateway.fetch()
    if response.error == "missing_identity":
        return _result(
            "needs_clarification",
            "No encontre una sesion local de Victus. Ejecuta `victus login` y vuelve a intentarlo.",
        )
    if response.error == "unreachable":
        return _result(
            "error",
            "No pude contactar el servidor web de Victus.",
            warning="backend_unreachable",
        )
    if response.status_code == 401:
        return _result(
            "blocked",
            "Tu sesion de Victus expiro. Ejecuta `victus login` nuevamente.",
            warning="session_expired",
        )
    if response.status_code != 200:
        return _result(
            "error",
            "El servidor web de Victus no pudo entregar tu perfil.",
            warning=f"backend_status_{response.status_code}",
        )
    profile = response.payload
    return ToolExecution(
        result=ToolResult(
            status="success",
            data={
                "summary": _profile_summary(profile),
                "profile": profile if isinstance(profile, dict) else None,
            },
            meta=ToolMeta(handler_version="recuperar_perfil.v1", trace_id=context.trace_id),
        )
    )


def _result(status: ToolStatus, summary: str, warning: str | None = None) -> ToolExecution:
    return ToolExecution(
        result=ToolResult(
            status=status,
            data={"summary": summary},
            warnings=[warning] if warning else [],
            meta=ToolMeta(handler_version="recuperar_perfil.v1"),
        )
    )


def _profile_summary(profile: Any) -> str:
    if not isinstance(profile, dict):
        return "Perfil Victus recuperado correctamente."
    parts = ["Perfil Victus recuperado correctamente."]
    for label, keys in (
        ("Nombre", ("display_name", "name", "full_name")),
        ("Email", ("email",)),
        ("Usuario", ("id", "user_id", "sub")),
        ("Plan", ("plan", "subscription")),
    ):
        if value := _first_string(profile, *keys):
            parts.append(f"{label}: {value}.")
    nested = profile.get("profile")
    if isinstance(nested, dict):
        for label, key in (
            ("Objetivos", "goals"),
            ("Restricciones", "restrictions"),
            ("Preferencias", "preferences"),
        ):
            if values := _string_list(nested.get(key)):
                parts.append(f"{label}: {', '.join(values)}.")
    return " ".join(parts)


def _first_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str) and item] if isinstance(value, list) else []

from __future__ import annotations

import os
from typing import Any

import httpx

from domain.tools.models import ToolMeta, ToolResult
from victus_mcp.utils.auth import get_valid_access_token

DEFAULT_BACKEND_API_URL = "http://localhost:8000/v1"
BACKEND_API_URL_ENV_VAR = "BACKEND_API_URL"
PROFILE_ENDPOINT = "/me"
REQUEST_TIMEOUT_SECONDS = 10.0


async def recuperar_perfil() -> ToolResult:
    token = await get_valid_access_token()
    if not token:
        return ToolResult(
            status="needs_clarification",
            data={
                "summary": (
                    "No encontre una sesion local de Victus. Ejecuta `victus login` en tu "
                    "terminal para autenticarte y vuelve a intentarlo."
                )
            },
            meta=ToolMeta(handler_version="recuperar_perfil.v1"),
        )

    url = _profile_url()
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    except httpx.HTTPError:
        return ToolResult(
            status="error",
            data={
                "summary": (
                    "No pude contactar el servidor web de Victus. Revisa tu conexion o la "
                    "variable BACKEND_API_URL y vuelve a intentarlo."
                )
            },
            warnings=["backend_unreachable"],
            meta=ToolMeta(handler_version="recuperar_perfil.v1"),
        )

    if response.status_code == 401:
        return ToolResult(
            status="blocked",
            data={
                "summary": (
                    "Tu sesion de Victus expiro o ya no es valida. Ejecuta `victus login` "
                    "nuevamente en tu terminal."
                )
            },
            warnings=["session_expired"],
            meta=ToolMeta(handler_version="recuperar_perfil.v1"),
        )

    if response.status_code != 200:
        return ToolResult(
            status="error",
            data={
                "summary": (
                    "El servidor web de Victus no pudo entregar tu perfil en este momento."
                )
            },
            warnings=[f"backend_status_{response.status_code}"],
            meta=ToolMeta(handler_version="recuperar_perfil.v1"),
        )

    try:
        profile = response.json()
    except ValueError:
        return ToolResult(
            status="error",
            data={"summary": "El servidor web devolvio una respuesta de perfil invalida."},
            warnings=["invalid_backend_json"],
            meta=ToolMeta(handler_version="recuperar_perfil.v1"),
        )

    return ToolResult(
        status="success",
        data={
            "summary": _profile_summary(profile),
            "profile": profile if isinstance(profile, dict) else None,
        },
        meta=ToolMeta(handler_version="recuperar_perfil.v1"),
    )


def _profile_url() -> str:
    base_url = os.getenv(BACKEND_API_URL_ENV_VAR, DEFAULT_BACKEND_API_URL).rstrip("/")
    return f"{base_url}{PROFILE_ENDPOINT}"


def _profile_summary(profile: Any) -> str:
    if not isinstance(profile, dict):
        return "Perfil Victus recuperado correctamente."

    display_name = _first_string(profile, "display_name", "name", "full_name")
    email = _first_string(profile, "email")
    user_id = _first_string(profile, "id", "user_id", "sub")
    plan = _first_string(profile, "plan", "subscription")

    parts = ["Perfil Victus recuperado correctamente."]
    if display_name:
        parts.append(f"Nombre: {display_name}.")
    if email:
        parts.append(f"Email: {email}.")
    if user_id:
        parts.append(f"Usuario: {user_id}.")
    if plan:
        parts.append(f"Plan: {plan}.")

    nested_profile = profile.get("profile")
    if isinstance(nested_profile, dict):
        goals = _string_list(nested_profile.get("goals"))
        restrictions = _string_list(nested_profile.get("restrictions"))
        preferences = _string_list(nested_profile.get("preferences"))
        if goals:
            parts.append(f"Objetivos: {', '.join(goals)}.")
        if restrictions:
            parts.append(f"Restricciones: {', '.join(restrictions)}.")
        if preferences:
            parts.append(f"Preferencias: {', '.join(preferences)}.")

    return " ".join(parts)


def _first_string(payload: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]

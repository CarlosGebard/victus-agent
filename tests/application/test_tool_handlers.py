from __future__ import annotations

import asyncio

import httpx

from application.tools import execute_tool, execute_tool_async, list_tools
from application.tools import remote_profile


def test_tool_registry_exposes_current_tools() -> None:
    assert [tool.name for tool in list_tools(visible_only=True)] == [
        "event_capture",
        "profile_update",
        "recuperar_perfil",
    ]


def test_event_capture_tool_returns_tool_result() -> None:
    result = execute_tool(
        "event_capture",
        {"user_id": "user-1", "normalized_text": "hoy comi arroz con pollo"},
    )

    assert result.status == "success"
    assert result.data["capture_action"] == "log_meal"
    assert result.meta.handler_version == "event_capture.v1"


def test_profile_update_tool_returns_tool_result() -> None:
    result = execute_tool(
        "profile_update",
        {"user_id": "user-1", "normalized_text": "soy intolerante a la lactosa"},
    )

    assert result.status == "success"
    assert result.data["profile_action"] == "add_restriction"
    assert result.meta.handler_version == "profile_update.v1"


def test_recuperar_perfil_returns_login_guidance_without_token(monkeypatch) -> None:
    monkeypatch.delenv("VICTUS_API_TOKEN", raising=False)

    async def token() -> None:
        return None

    monkeypatch.setattr(remote_profile, "get_valid_access_token", token)

    result = asyncio.run(execute_tool_async("recuperar_perfil", {}))

    assert result.status == "needs_clarification"
    assert "victus login" in result.data["summary"]


def test_recuperar_perfil_returns_profile_summary(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_API_URL", "https://backend.test/v1")

    async def token() -> str:
        return "test-token"

    monkeypatch.setattr(remote_profile, "get_valid_access_token", token)
    monkeypatch.setattr(remote_profile.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeResponse(
        200,
        {
            "id": "user-1",
            "email": "user@example.com",
            "display_name": "Carlos",
            "plan": "free",
            "profile": {
                "goals": ["nutrition_tracking"],
                "restrictions": ["lactose_intolerance"],
                "preferences": ["high_protein"],
            },
        },
    )

    result = asyncio.run(execute_tool_async("recuperar_perfil", {}))

    assert FakeAsyncClient.last_url == "https://backend.test/v1/me"
    assert FakeAsyncClient.last_headers == {"Authorization": "Bearer test-token"}
    assert result.status == "success"
    assert "Carlos" in result.data["summary"]
    assert "lactose_intolerance" in result.data["summary"]


def test_recuperar_perfil_handles_expired_session(monkeypatch) -> None:
    async def token() -> str:
        return "expired-token"

    monkeypatch.setattr(remote_profile, "get_valid_access_token", token)
    monkeypatch.setattr(remote_profile.httpx, "AsyncClient", FakeAsyncClient)
    FakeAsyncClient.response = FakeResponse(401, {"error": "unauthorized"})

    result = asyncio.run(execute_tool_async("recuperar_perfil", {}))

    assert result.status == "blocked"
    assert "victus login" in result.data["summary"]
    assert result.warnings == ["session_expired"]


def test_recuperar_perfil_handles_network_errors(monkeypatch) -> None:
    async def token() -> str:
        return "test-token"

    monkeypatch.setattr(remote_profile, "get_valid_access_token", token)
    monkeypatch.setattr(remote_profile.httpx, "AsyncClient", FailingAsyncClient)

    result = asyncio.run(execute_tool_async("recuperar_perfil", {}))

    assert result.status == "error"
    assert result.warnings == ["backend_unreachable"]


class FakeResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload


class FakeAsyncClient:
    response = FakeResponse(200, {})
    last_url: str | None = None
    last_headers: dict[str, str] | None = None

    def __init__(self, *, timeout: float) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def get(self, url: str, *, headers: dict[str, str]) -> FakeResponse:
        FakeAsyncClient.last_url = url
        FakeAsyncClient.last_headers = headers
        return FakeAsyncClient.response


class FailingAsyncClient(FakeAsyncClient):
    async def get(self, url: str, *, headers: dict[str, str]) -> FakeResponse:
        raise httpx.ConnectError("connection failed")

import pytest

from application.tools import execute_tool


def test_execute_unknown_tool_raises() -> None:
    with pytest.raises(ValueError):
        execute_tool("unknown", {})


def test_mcp_server_registers_current_tools_when_sdk_available() -> None:
    pytest.importorskip("mcp")

    from victus_mcp.server import build_server

    server = build_server()

    assert server is not None


def test_mcp_http_app_exposes_health_and_mcp_mount() -> None:
    pytest.importorskip("mcp")

    from starlette.testclient import TestClient
    from victus_mcp.http_server import MCP_PATH, create_app

    app = create_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "victus-agent-mcp-http",
        "transport": "streamable_http",
    }
    assert any(getattr(route, "path", "") == MCP_PATH for route in app.routes)

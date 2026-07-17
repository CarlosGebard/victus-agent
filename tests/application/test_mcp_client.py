from __future__ import annotations

from application.mcp import MCPClientConfig, VictusMCPClient


def test_mcp_client_passes_inherited_and_configured_environment(monkeypatch) -> None:
    monkeypatch.setenv("VICTUS_API_TOKEN", "env-token")

    params = VictusMCPClient(
        MCPClientConfig(env={"BACKEND_API_URL": "https://backend.test/v1"})
    )._server_params()

    assert params.env["VICTUS_API_TOKEN"] == "env-token"
    assert params.env["BACKEND_API_URL"] == "https://backend.test/v1"

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

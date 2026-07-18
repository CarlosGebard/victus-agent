import asyncio

from adapters.cli.commands import inspect_tool, list_tool_data
from adapters.langgraph.graph import build_graph
from adapters.mcp.discovery import discover_tools
from victus_platform.llm.contracts import LLMRequest, LLMResponse


def test_langgraph_executes_runtime_and_blocks_unsafe_turns() -> None:
    allowed = asyncio.run(
        build_graph().ainvoke({"request": {"raw_text": "hoy comi arroz"}})
    )
    assert allowed["tool_context"]["last_tool_result"]["data"]["capture_action"] == "log_meal"
    assert allowed["audit"]["node_path"][-1] == "event_capture"

    blocked = asyncio.run(
        build_graph(llm_client=BlockedSafetyClient()).ainvoke(
            {"request": {"raw_text": "I am going to hurt myself"}}
        )
    )
    assert blocked["safety"]["status"] == "blocked"
    assert blocked["tool_context"]["allowed_tools"] == []
    assert "last_tool_result" not in blocked["tool_context"]


def test_mcp_discovers_catalog_and_serves_http_health() -> None:
    from starlette.testclient import TestClient

    from adapters.mcp.transport import MCP_PATH, create_app

    assert [tool.name for tool in discover_tools()][0] == "event_capture"
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["transport"] == "streamable_http"
    assert MCP_PATH == "/mcp"


def test_cli_reads_catalog_without_alternate_execution_metadata() -> None:
    assert list_tool_data()[0]["name"] == "event_capture"
    inspected = inspect_tool("event_capture")
    assert inspected["input_schema"]["title"] == "EventCaptureInput"


class BlockedSafetyClient:
    def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(text="unsafe\nS11")

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("unexpected async safety call")

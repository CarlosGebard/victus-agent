from __future__ import annotations

import asyncio

from agent.graph import build_graph
from application.ports.llm import LLMRequest, LLMResponse


def test_graph_runs_only_event_capture_node_for_meal_input() -> None:
    graph = build_graph()

    result = asyncio.run(graph.ainvoke({"request": {"raw_text": "hoy comi arroz"}}))

    assert result["request"] == {
        "original_text": "hoy comi arroz",
        "working_text": "hoy comi arroz",
    }
    assert result["intent"]["target_node"] == "event_capture"
    assert result["tool_context"]["last_tool_result"]["tool_name"] == "event_capture"
    assert result["tool_context"]["last_tool_result"]["data"]["capture_action"] == "log_meal"
    assert result["audit"]["node_path"] == ["normalize_request", "safety_precheck", "event_capture"]


def test_graph_event_capture_reroutes_non_capture_input() -> None:
    graph = build_graph()

    result = asyncio.run(graph.ainvoke({"request": {"raw_text": "hazme un plan"}}))

    data = result["tool_context"]["last_tool_result"]["data"]
    assert data["capture_action"] == "reroute"
    assert data["selected_skill"] == "none"
    assert result["audit"]["node_path"] == ["normalize_request", "safety_precheck", "event_capture"]


def test_graph_routes_blocked_safety_to_warning_response_without_tools() -> None:
    graph = build_graph(llm_client=BlockedSafetyClient())

    result = asyncio.run(graph.ainvoke({"request": {"raw_text": "I am going to hurt myself"}}))

    assert result["safety"]["status"] == "blocked"
    assert result["safety"]["categories"] == ["self_harm"]
    assert result["intent"]["target_node"] == "safety_blocked_response"
    assert result["response"]["mode"] == "blocked"
    assert result["tool_context"]["allowed_tools"] == []
    assert "last_tool_result" not in result["tool_context"]
    assert result["audit"]["node_path"] == [
        "normalize_request",
        "safety_precheck",
        "safety_blocked_response",
    ]


class BlockedSafetyClient:
    def complete(self, request: LLMRequest) -> LLMResponse:
        assert request.operation == "agent.safety_precheck.llama_guard"
        return LLMResponse(text="unsafe\nS11")

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        raise AssertionError("blocked safety graph path should not call async completion")

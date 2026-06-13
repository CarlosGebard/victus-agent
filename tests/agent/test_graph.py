from __future__ import annotations

import asyncio

import pytest

from agent.graph import build_graph
from application.ports.llm import LLMRequest, LLMResponse
from victus_routing.models import RouteDecision


class StubRouter:
    def __init__(self, route: str = "EventCaptureGraph") -> None:
        self.route_name = route

    def route(self, input_text: str) -> RouteDecision:
        return RouteDecision(
            router_version="test",
            input_text=input_text,
            normalized_text=input_text.lower(),
            decision="route",
            route=self.route_name,
            intent_type="log_update_data",
            confidence=0.9,
        )


class StubLLMClient:
    def __init__(self) -> None:
        self.requests: list[LLMRequest] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(text="sync")

    async def acomplete(self, request: LLMRequest) -> LLMResponse:
        self.requests.append(request)
        return LLMResponse(text="llm response")


def test_graph_routes_and_composes_deterministic_response() -> None:
    graph = build_graph(router=StubRouter())

    result = graph.invoke({"request": {"raw_text": "hoy comi arroz"}})

    assert result["request"]["normalized_text"] == "hoy comi arroz"
    assert result["intent"]["target_node"] == "EventCaptureGraph"
    assert result["response"]["user_message"] == "Route selected: EventCaptureGraph"
    assert result["audit"]["node_path"] == [
        "normalize_request",
        "safety_precheck",
        "route_intent",
        "compose_response",
    ]


def test_graph_composes_response_through_llm_port() -> None:
    llm_client = StubLLMClient()
    graph = build_graph(router=StubRouter("PlanningSessionGraph"), llm_client=llm_client)

    result = asyncio.run(graph.ainvoke({"request": {"raw_text": "hazme un plan"}}))

    assert result["response"]["user_message"] == "llm response"
    assert llm_client.requests[0].operation == "agent.compose_response"
    assert llm_client.requests[0].model == "litellm_proxy/gemini-flash-lite"

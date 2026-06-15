from __future__ import annotations

import asyncio

import pytest

from agent.graph import build_graph
from application.ports.llm import LLMRequest, LLMResponse
from domain.session_context.models import PendingInteractionState
from application.routing.models import RouteDecision


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
        if request.operation == "agent.context_bootstrap.translate_normalized_text":
            return LLMResponse(text="make me a plan")
        return LLMResponse(text="llm response")


class StubSessionContextRepository:
    def __init__(self) -> None:
        self.saved_summaries = []
        self.cleared_pending = []

    def get_latest_summary(self, conversation_id: str):
        return None

    def get_pending_interaction(self, conversation_id: str):
        return PendingInteractionState(
            conversation_id=conversation_id,
            user_id="user-1",
            pending_kind="confirmation",
            assistant_prompt="Do you want to move dinner to tomorrow?",
            expected_user_response="yes_no",
            resume_graph="PlanRevisionGraph",
            resume_node="apply_plan_adjustment",
            created_at="2026-06-14T00:00:00+00:00",
            updated_at="2026-06-14T00:00:00+00:00",
        )

    def save_summary(self, summary):
        self.saved_summaries.append(summary)

    def save_pending_interaction(self, pending):
        raise AssertionError("no pending interaction should be saved for final responses")

    def clear_pending_interaction(self, conversation_id: str):
        self.cleared_pending.append(conversation_id)


def test_graph_routes_and_composes_deterministic_response() -> None:
    graph = build_graph(router=StubRouter())

    result = graph.invoke({"request": {"raw_text": "hoy comi arroz"}})

    assert result["request"] == {"original_text": "hoy comi arroz", "working_text": "hoy comi arroz"}
    assert result["intent"]["target_node"] == "EventCaptureGraph"
    assert result["response"]["user_message"] == "Route selected: EventCaptureGraph"
    assert result["audit"]["node_path"] == [
        "normalize_request",
        "context_bootstrap",
        "safety_precheck",
        "route_intent",
        "compose_response",
        "summarize_after_response",
    ]


def test_graph_composes_response_through_llm_port() -> None:
    llm_client = StubLLMClient()
    graph = build_graph(router=StubRouter("PlanningSessionGraph"), llm_client=llm_client)

    result = asyncio.run(graph.ainvoke({"request": {"raw_text": "hazme un plan"}}))

    assert result["response"]["user_message"] == "llm response"
    assert result["request"]["working_text"] == "make me a plan"
    assert llm_client.requests[0].operation == "agent.context_bootstrap.translate_normalized_text"
    assert llm_client.requests[0].model == "groq/llama-3.1-8b-instant"
    assert llm_client.requests[1].operation == "agent.compose_response"
    assert llm_client.requests[1].model == "litellm_proxy/gemini-flash-lite"


def test_graph_bootstraps_pending_context_before_routing() -> None:
    repository = StubSessionContextRepository()
    router = StubRouter("PlanRevisionGraph")
    graph = build_graph(router=router, session_context_repository=repository)

    result = graph.invoke(
        {
            "request": {
                "raw_text": "si, mañana",
                "user_id": "user-1",
                "conversation_id": "conversation-1",
            }
        }
    )

    assert "Pending interaction context" in result["request"]["working_text"]
    assert "move dinner to tomorrow" in result["request"]["working_text"]
    assert result["session_context"]["updated_summary"].current_topic == "PlanRevisionGraph"
    assert repository.saved_summaries
    assert repository.cleared_pending == ["conversation-1"]


def test_graph_routes_explicit_self_harm_to_emergency_support_response() -> None:
    graph = build_graph(router=StubRouter())

    result = graph.invoke(
        {
            "request": {
                "original_text": "necesito ayuda",
                "working_text": "i want to kill myself",
            }
        }
    )

    assert result["safety"]["decision"] == "emergency_escalation"
    assert result["safety"]["matched_rules"] == ["self_harm.explicit_suicidal_intent"]
    assert result["response"]["mode"] == "emergency_support"
    assert "988" in result["response"]["user_message"]
    assert result["audit"]["node_path"] == [
        "normalize_request",
        "context_bootstrap",
        "safety_precheck",
        "self_harm_response",
        "summarize_after_response",
    ]


def test_graph_routes_high_self_harm_to_adjacent_safety_response() -> None:
    graph = build_graph(router=StubRouter())

    result = graph.invoke(
        {
            "request": {
                "original_text": "me quiero hacer dano",
                "working_text": "i am going to hurt myself",
            }
        }
    )

    assert result["safety"]["decision"] == "route_to_safety_triage"
    assert result["response"]["mode"] == "safety_triage"
    assert "route_intent" not in result["audit"]["node_path"]

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from adapters.langgraph.context import normalize_request, safety_blocked_response, safety_precheck
from adapters.langgraph.state import VictusGraphState
from victus_platform.llm.contracts import LLMClient
from adapters.langgraph.routing import route_after_safety
from adapters.langgraph.tool_node import tool_node
from bootstrap.runtime import build_runtime


def build_graph(
    *,
    llm_client: LLMClient | None = None,
    session_context_repository=None,
    tool_runtime=None,
):
    tool_runtime = tool_runtime or build_runtime()
    graph_builder = StateGraph(VictusGraphState)
    graph_builder.add_node("normalize_request", normalize_request)
    graph_builder.add_node(
        "safety_precheck",
        safety_precheck(
            llm_client=llm_client,
            model="meta-llama/Llama-Guard-4-12B:together" if llm_client else None,
        ),
    )
    graph_builder.add_node("safety_blocked_response", safety_blocked_response)
    graph_builder.add_node("event_capture", tool_node("event_capture", tool_runtime))

    graph_builder.add_edge(START, "normalize_request")
    graph_builder.add_edge("normalize_request", "safety_precheck")
    graph_builder.add_conditional_edges(
        "safety_precheck",
        route_after_safety,
        {
            "blocked": "safety_blocked_response",
            "allowed": "event_capture",
        },
    )
    graph_builder.add_edge("safety_blocked_response", END)
    graph_builder.add_edge("event_capture", END)
    return graph_builder.compile()


def _build_studio_graph():
    return build_graph()


graph = _build_studio_graph()

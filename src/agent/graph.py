from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.nodes.context import context_bootstrap
from agent.nodes.runtime import compose_response, normalize_request, safety_precheck, tool_registry
from agent.nodes.self_harm_response import self_harm_response
from agent.nodes.summary import summarize_after_response
from agent.state import VictusGraphState
from application.config import load_runtime_config
from application.ports.llm import LLMClient


def build_graph(
    *,
    llm_client: LLMClient | None = None,
    session_context_repository=None,
):
    runtime_config = load_runtime_config()
    graph_builder = StateGraph(VictusGraphState)
    graph_builder.add_node("normalize_request", normalize_request)
    graph_builder.add_node(
        "safety_precheck",
        safety_precheck(llm_client=llm_client, model=runtime_config.safety.model),
    )
    graph_builder.add_node(
        "context_bootstrap",
        context_bootstrap(session_context_repository, llm_client=llm_client),
    )
    graph_builder.add_node("self_harm_response", self_harm_response())
    graph_builder.add_node("tool_registry", tool_registry)
    graph_builder.add_node(
        "compose_response",
        compose_response(llm_client=llm_client, model=runtime_config.llm.model),
    )
    graph_builder.add_node(
        "summarize_after_response",
        summarize_after_response(session_context_repository),
    )

    graph_builder.add_edge(START, "safety_precheck")
    graph_builder.add_edge("safety_precheck", "normalize_request")
    graph_builder.add_edge("normalize_request", "context_bootstrap")
    graph_builder.add_conditional_edges(
        "context_bootstrap",
        _next_after_safety_precheck,
        {
            "self_harm_response": "self_harm_response",
            "tool_registry": "tool_registry",
        },
    )
    graph_builder.add_edge("self_harm_response", "summarize_after_response")
    graph_builder.add_edge("tool_registry", "compose_response")
    graph_builder.add_edge("compose_response", "summarize_after_response")
    graph_builder.add_edge("summarize_after_response", END)
    return graph_builder.compile()


def _next_after_safety_precheck(state: VictusGraphState) -> str:
    safety = state.get("safety", {})
    categories = set(safety.get("categories", []))
    if "self_harm" in categories and safety.get("severity") in {"high", "critical"}:
        return "self_harm_response"
    return "tool_registry"


def _build_studio_graph():
    from infrastructure.llm.factory import build_llm_client

    return build_graph(llm_client=build_llm_client())


graph = _build_studio_graph()

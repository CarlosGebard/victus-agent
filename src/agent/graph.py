from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.nodes.runtime import _merge, normalize_request, safety_blocked_response, safety_precheck
from agent.state import VictusGraphState
from application.ports.llm import LLMClient
from application.text import normalize_text
from application.tools import execute_tool


def build_graph(
    *,
    llm_client: LLMClient | None = None,
    session_context_repository=None,
):
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
    graph_builder.add_node("event_capture", _event_capture)

    graph_builder.add_edge(START, "normalize_request")
    graph_builder.add_edge("normalize_request", "safety_precheck")
    graph_builder.add_conditional_edges(
        "safety_precheck",
        _route_after_safety,
        {
            "blocked": "safety_blocked_response",
            "allowed": "event_capture",
        },
    )
    graph_builder.add_edge("safety_blocked_response", END)
    graph_builder.add_edge("event_capture", END)
    return graph_builder.compile()


def _event_capture(state: VictusGraphState) -> VictusGraphState:
    request = dict(state.get("request", {}))
    original_text = str(
        request.get("original_text")
        or request.get("raw_text")
        or request.get("working_text")
        or ""
    )
    working_text = str(request.get("working_text") or normalize_text(original_text))
    user_id = str(request.get("user_id") or "local-user")

    tool_result = execute_tool(
        "event_capture",
        {
            "user_id": user_id,
            "normalized_text": working_text,
            "active_clarification_exists": False,
        },
    )

    request.pop("raw_text", None)
    request["original_text"] = original_text
    request["working_text"] = working_text

    tool_context = dict(state.get("tool_context", {}))
    tool_context["last_tool_result"] = {
        "tool_name": "event_capture",
        **tool_result.model_dump(mode="json"),
    }
    data = tool_result.data if isinstance(tool_result.data, dict) else {}

    return _merge(
        state,
        request=request,
        tool_context=tool_context,
        intent={
            "primary_intent": "event_capture",
            "confidence": 1.0,
            "target_node": "event_capture",
            "subintents": [],
            "rationale": data.get("reason", ""),
        },
        node_name="event_capture",
    )


def _route_after_safety(state: VictusGraphState) -> str:
    safety = state.get("safety", {})
    if safety.get("status") == "blocked":
        return "blocked"
    return "allowed"


def _build_studio_graph():
    return build_graph()


graph = _build_studio_graph()

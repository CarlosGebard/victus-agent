from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from adapters.langgraph.engine.agent import (
    agent_decision,
    clarification_interrupt,
    compose_final_response,
    confirmation_interrupt,
    execute_tool,
    finalize_turn,
    ingest_turn,
    route_after_confirmation,
    route_after_decision,
    route_after_execution,
)
from adapters.langgraph.runtime.context import (
    normalize_request,
    safety_blocked_response,
    safety_precheck,
    tool_registry,
)
from adapters.langgraph.capabilities.projections import load_domain_projections
from adapters.langgraph.engine.routing import route_after_safety
from adapters.langgraph.engine.state import VictusGraphState
from adapters.langgraph.runtime.memory import recall_long_term_memory, update_long_term_memory
from bootstrap.runtime import build_runtime, projection_repository_scope
from victus_platform.config.runtime import load_runtime_config
from victus_platform.llm.contracts import LLMClient
from victus_platform.llm.factory import build_llm_client


def build_graph(
    *,
    llm_client: LLMClient | None = None,
    safety_client: LLMClient | None = None,
    tool_runtime=None,
    checkpointer=None,
    store=None,
    projection_scope=None,
):
    runtime_config = load_runtime_config()
    tool_runtime = tool_runtime or build_runtime()
    graph_builder = StateGraph(VictusGraphState)
    graph_builder.add_node("ingest_turn", ingest_turn)
    graph_builder.add_node("normalize_request", normalize_request)
    graph_builder.add_node("recall_long_term_memory", recall_long_term_memory(store))
    graph_builder.add_node(
        "load_domain_projections",
        load_domain_projections(projection_scope),
    )
    graph_builder.add_node(
        "safety_precheck",
        safety_precheck(
            llm_client=safety_client,
            model=runtime_config.safety.model if safety_client else None,
        ),
    )
    graph_builder.add_node("safety_blocked_response", safety_blocked_response)
    graph_builder.add_node("tool_registry", tool_registry)
    graph_builder.add_node(
        "agent_decision",
        agent_decision(llm_client=llm_client, model=runtime_config.llm.model),
    )
    graph_builder.add_node("confirmation_interrupt", confirmation_interrupt)
    graph_builder.add_node("execute_tool", execute_tool(tool_runtime))
    graph_builder.add_node("clarification_interrupt", clarification_interrupt)
    graph_builder.add_node("compose_final_response", compose_final_response)
    graph_builder.add_node("update_long_term_memory", update_long_term_memory(store))
    graph_builder.add_node("finalize_turn", finalize_turn)

    graph_builder.add_edge(START, "ingest_turn")
    graph_builder.add_edge("ingest_turn", "normalize_request")
    graph_builder.add_edge("normalize_request", "recall_long_term_memory")
    graph_builder.add_edge("recall_long_term_memory", "load_domain_projections")
    graph_builder.add_edge("load_domain_projections", "safety_precheck")
    graph_builder.add_conditional_edges(
        "safety_precheck",
        route_after_safety,
        {"blocked": "safety_blocked_response", "allowed": "tool_registry"},
    )
    graph_builder.add_edge("safety_blocked_response", "update_long_term_memory")
    graph_builder.add_edge("tool_registry", "agent_decision")
    graph_builder.add_conditional_edges(
        "agent_decision",
        route_after_decision,
        {
            "response": "compose_final_response",
            "confirm": "confirmation_interrupt",
            "execute": "execute_tool",
        },
    )
    graph_builder.add_conditional_edges(
        "confirmation_interrupt",
        route_after_confirmation,
        {"response": "compose_final_response", "execute": "execute_tool"},
    )
    graph_builder.add_conditional_edges(
        "execute_tool",
        route_after_execution,
        {
            "clarify": "clarification_interrupt",
            "decide": "agent_decision",
            "response": "compose_final_response",
        },
    )
    graph_builder.add_edge("clarification_interrupt", "agent_decision")
    graph_builder.add_edge("compose_final_response", "update_long_term_memory")
    graph_builder.add_edge("update_long_term_memory", "finalize_turn")
    graph_builder.add_edge("finalize_turn", END)
    return graph_builder.compile(checkpointer=checkpointer, store=store)


def _build_studio_graph():
    client = build_llm_client()
    return build_graph(
        llm_client=client,
        projection_scope=projection_repository_scope,
    )


graph = _build_studio_graph()

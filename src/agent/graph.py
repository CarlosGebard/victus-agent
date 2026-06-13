from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from agent.nodes.runtime import compose_response, normalize_request, route_intent, safety_precheck
from agent.state import VictusGraphState
from application.config import load_runtime_config
from application.ports.llm import LLMClient
from victus_routing.embeddings import DeterministicHashEmbedder
from victus_routing.policy import RoutingPolicy
from victus_routing.prototype_store import PrototypeStore, load_thresholds
from victus_routing.router import IntentRouter
from victus_routing.safety_gate import SafetyGate


def build_graph(*, router: IntentRouter | None = None, llm_client: LLMClient | None = None):
    runtime_config = load_runtime_config()
    graph_builder = StateGraph(VictusGraphState)
    graph_builder.add_node("normalize_request", normalize_request)
    graph_builder.add_node("safety_precheck", safety_precheck)
    graph_builder.add_node("route_intent", route_intent(router or build_default_router()))
    graph_builder.add_node(
        "compose_response",
        compose_response(llm_client=llm_client, model=runtime_config.llm.model),
    )

    graph_builder.add_edge(START, "normalize_request")
    graph_builder.add_edge("normalize_request", "safety_precheck")
    graph_builder.add_edge("safety_precheck", "route_intent")
    graph_builder.add_edge("route_intent", "compose_response")
    graph_builder.add_edge("compose_response", END)
    return graph_builder.compile()


def build_default_router() -> IntentRouter:
    prototype_store = PrototypeStore.from_yaml("config/router/intent_prototypes.v1.yml")
    router_version, thresholds, weights = load_thresholds("config/router/router_thresholds.v1.yml")
    return IntentRouter(
        embedder=DeterministicHashEmbedder(),
        prototype_store=prototype_store,
        policy=RoutingPolicy(router_version=router_version, thresholds=thresholds),
        safety_gate=SafetyGate(),
        weights=weights,
    )


graph = build_graph()

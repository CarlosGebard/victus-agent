from adapters.langgraph.engine.state import VictusGraphState


def route_after_safety(state: VictusGraphState) -> str:
    return "blocked" if state.get("safety", {}).get("status") == "blocked" else "allowed"

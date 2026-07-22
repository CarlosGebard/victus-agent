from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Callable

from adapters.langgraph.engine.state import VictusGraphState
from adapters.langgraph.runtime.context import _merge


def load_domain_projections(repository_scope: Callable[[], Any] | None = None):
    def node(state: VictusGraphState) -> VictusGraphState:
        user_id = str(state.get("request", {}).get("user_id") or "")
        projections: dict[str, Any] = {"loaded_at": datetime.now(UTC).isoformat()}
        if repository_scope is not None and user_id:
            with repository_scope() as repository:
                if repository is not None:
                    values = {
                        "user_profile": repository.get_user_profile(user_id),
                        "constraint": repository.get_constraint(user_id),
                        "nutrition_status": repository.get_nutrition_status(user_id),
                        "planning_history": repository.get_planning_history(user_id),
                    }
                    projections.update(
                        {
                            key: value.model_dump(mode="json")
                            for key, value in values.items()
                            if value is not None
                        }
                    )
                    sequences = [
                        value.last_event_seq
                        for value in values.values()
                        if value is not None and hasattr(value, "last_event_seq")
                    ]
                    projections["max_event_seq"] = max(sequences, default=0)
        return _merge(state, projections=projections, node_name="load_domain_projections")

    return node

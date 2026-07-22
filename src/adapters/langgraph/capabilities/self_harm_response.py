from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from adapters.langgraph.engine.state import VictusGraphState
from adapters.langgraph.runtime.context import _merge

DEFAULT_RESPONSE_POLICY = Path("safety/policies/self_harm_responses.yaml")
DEFAULT_POLICY = {
    "responses": {
        "high": {
            "mode": "safety_triage",
            "user_message": (
                "No puedo ayudar con esa accion de forma segura. Si hay riesgo inmediato, "
                "contacta servicios de emergencia o una linea de crisis local ahora."
            ),
        },
        "critical": {
            "mode": "safety_triage",
            "user_message": (
                "No puedo ayudar con esa accion de forma segura. Si hay riesgo inmediato, "
                "contacta servicios de emergencia o una linea de crisis local ahora."
            ),
        },
    }
}


def self_harm_response(policy_path: str | Path = DEFAULT_RESPONSE_POLICY):
    policy = _load_policy(policy_path)

    def node(state: VictusGraphState) -> VictusGraphState:
        safety = state.get("safety", {})
        categories = set(safety.get("categories", []))
        severity = str(safety.get("severity", "none"))
        if "self_harm" not in categories or severity not in {"high", "critical"}:
            return _merge(state, node_name="self_harm_response")

        response = policy["responses"][severity]
        return _merge(
            state,
            response={
                "mode": response["mode"],
                "user_message": response["user_message"],
                "internal_notes": list(safety.get("reason_codes", [])),
            },
            node_name="self_harm_response",
        )

    return node


def _load_policy(path: str | Path) -> dict[str, Any]:
    policy_path = Path(path)
    if not policy_path.exists():
        return DEFAULT_POLICY
    with policy_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict) or not isinstance(data.get("responses"), dict):
        raise ValueError(f"self-harm response policy must contain responses mapping: {path}")
    return data

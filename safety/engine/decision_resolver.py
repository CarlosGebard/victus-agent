from __future__ import annotations

from pathlib import Path
from typing import Any

from safety.engine.rule_loader import load_yaml_mapping
from safety.engine.schemas import (
    SEVERITY_RANK,
    SafetyPrecheckResult,
    SafetySignal,
)

DEFAULT_DECISION_MATRIX = Path("safety/policies/decision_matrix.yaml")
DEFAULT_TOOL_GATES = Path("safety/policies/tool_gates.yaml")


def resolve_decision(
    signals: list[SafetySignal],
    *,
    decision_matrix_path: str | Path = DEFAULT_DECISION_MATRIX,
    tool_gates_path: str | Path = DEFAULT_TOOL_GATES,
) -> SafetyPrecheckResult:
    positive = _drop_negated(signals)
    if not positive:
        return SafetyPrecheckResult.allow()

    strongest = max(positive, key=lambda item: (SEVERITY_RANK[item.severity], item.priority))
    matrix_entry = _lookup_policy(load_yaml_mapping(decision_matrix_path), strongest)
    gates_entry = _lookup_policy(load_yaml_mapping(tool_gates_path), strongest)
    categories = sorted({signal.category for signal in positive})

    return SafetyPrecheckResult(
        decision=matrix_entry["decision"],
        severity=strongest.severity,
        categories=categories,
        matched_rules=[signal.rule_id for signal in positive],
        reason_codes=sorted({signal.reason_code for signal in positive}),
        blocked_tools=list(gates_entry.get("blocked_tools", [])),
        allowed_next_route=matrix_entry["allowed_next_route"],
        audit_required=bool(matrix_entry.get("audit_required", True)),
    )


def _drop_negated(signals: list[SafetySignal]) -> list[SafetySignal]:
    return [signal for signal in signals if not signal.negative]


def _lookup_policy(policy: dict[str, Any], signal: SafetySignal) -> dict[str, Any]:
    for entry in policy.get("rules", []):
        if entry.get("category") == signal.category and entry.get("severity") == signal.severity:
            return entry
    default = policy.get("default", {})
    if not isinstance(default, dict):
        raise ValueError("policy default must be a mapping")
    return default

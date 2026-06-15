from __future__ import annotations

import re
from typing import Any

from application.routing.normalizer import normalize_text
from safety.engine.schemas import SafetyRule, SafetySignal


def evaluate_rules(text: str, rules: list[SafetyRule]) -> list[SafetySignal]:
    normalized = normalize_text(text)
    return [_to_signal(rule) for rule in rules if _matches(rule.match, normalized)]


def _to_signal(rule: SafetyRule) -> SafetySignal:
    return SafetySignal(
        rule_id=rule.id,
        category=rule.category,
        severity=rule.severity,
        priority=rule.priority,
        reason_code=rule.reason_code,
        negative=rule.negative,
    )


def _matches(spec: dict[str, Any], text: str) -> bool:
    if phrase := spec.get("phrase"):
        return str(phrase).lower() in text
    if regex := spec.get("regex"):
        return re.search(str(regex), text) is not None
    if any_items := spec.get("any"):
        return any(_matches(_as_mapping(item), text) for item in _as_list(any_items))
    if all_items := spec.get("all"):
        return all(_matches(_as_mapping(item), text) for item in _as_list(all_items))
    if not_item := spec.get("not"):
        return not _matches(_as_mapping(not_item), text)
    raise ValueError(f"unsupported match expression: {spec}")


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("match operator expects a list")
    return value


def _as_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("match operator expects a mapping")
    return value

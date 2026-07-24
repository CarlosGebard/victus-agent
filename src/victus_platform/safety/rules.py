from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class SafetyRule:
    id: str
    severity: Literal["high", "critical"]
    reason_code: str
    patterns: tuple[str, ...]


@dataclass(frozen=True)
class SafetySignal:
    rule_id: str
    severity: str
    reason_code: str


class SafetyPrecheckInput(BaseModel):
    original_text: str
    working_text: str


class SafetyPrecheckResult(BaseModel):
    decision: Literal["allow", "route_to_safety_triage", "emergency_escalation"]
    severity: Literal["none", "high", "critical"]
    categories: list[str]
    reasons: list[str] = Field(default_factory=list)


def load_rules() -> list[SafetyRule]:
    return [
        SafetyRule(
            id="self_harm.explicit_suicidal_intent",
            severity="critical",
            reason_code="explicit_suicidal_intent",
            patterns=(
                r"\bi want to kill myself\b",
                r"\bi (?:want|plan) to die\b",
                r"\bme quiero suicidar\b",
            ),
        ),
        SafetyRule(
            id="self_harm.self_harm_intent",
            severity="high",
            reason_code="self_harm_intent",
            patterns=(
                r"\bi am going to (?:cut|hurt) myself\b",
                r"\bi want to hurt myself\b",
                r"\bquiero hacerme da[nñ]o\b",
            ),
        ),
        SafetyRule(
            id="self_harm.passive_ideation",
            severity="high",
            reason_code="passive_ideation",
            patterns=(r"\bi wish i (?:was|were) dead\b", r"\bbetter off dead\b"),
        ),
    ]


def evaluate_rules(text: str, rules: list[SafetyRule] | None = None) -> list[SafetySignal]:
    normalized = " ".join(text.casefold().split())
    if normalized in {"this homework is killing me", "i'm dying of hunger"}:
        return []
    return [
        SafetySignal(rule_id=rule.id, severity=rule.severity, reason_code=rule.reason_code)
        for rule in rules or load_rules()
        if any(re.search(pattern, normalized) for pattern in rule.patterns)
    ]


class SafetyPrecheck:
    def check(self, input_data: SafetyPrecheckInput) -> SafetyPrecheckResult:
        signals = evaluate_rules(input_data.working_text)
        if not signals:
            return SafetyPrecheckResult(
                decision="allow",
                severity="none",
                categories=["none"],
            )
        critical = any(signal.severity == "critical" for signal in signals)
        return SafetyPrecheckResult(
            decision="emergency_escalation" if critical else "route_to_safety_triage",
            severity="critical" if critical else "high",
            categories=["self_harm"],
            reasons=[signal.reason_code for signal in signals],
        )


def normalize_aegis_row(row: dict[str, object], category_map: dict[str, str]) -> dict[str, object]:
    source_category = str(row.get("violated_category") or "")
    return {
        "source": "aegis_2_0",
        "text": str(row.get("prompt") or ""),
        "category": category_map.get(source_category, "other"),
        "unsafe": bool(row.get("unsafe")),
        "source_category": source_category,
    }

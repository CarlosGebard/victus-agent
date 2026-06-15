from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SafetyDecision = Literal["allow", "route_to_safety_triage", "emergency_escalation"]
SafetySeverity = Literal["none", "low", "medium", "high", "critical"]
SafetyCategory = Literal["none", "self_harm"]
SafetyRoute = Literal["IntentRouter", "SafetyTriageRoute", "EmergencySupportResponse"]

SEVERITY_RANK: dict[SafetySeverity, int] = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}


@dataclass(frozen=True)
class SafetyRule:
    id: str
    category: SafetyCategory
    severity: SafetySeverity
    priority: int
    reason_code: str
    match: dict[str, Any]
    enabled: bool = True
    negative: bool = False


@dataclass(frozen=True)
class SafetySignal:
    rule_id: str
    category: SafetyCategory
    severity: SafetySeverity
    priority: int
    reason_code: str
    negative: bool = False


@dataclass(frozen=True)
class SafetyPrecheckInput:
    original_text: str
    working_text: str
    session_summary: object | None = None


@dataclass(frozen=True)
class SafetyPrecheckResult:
    decision: SafetyDecision
    severity: SafetySeverity
    categories: list[SafetyCategory]
    matched_rules: list[str]
    reason_codes: list[str]
    blocked_tools: list[str]
    allowed_next_route: SafetyRoute
    audit_required: bool

    @classmethod
    def allow(cls) -> SafetyPrecheckResult:
        return cls(
            decision="allow",
            severity="none",
            categories=["none"],
            matched_rules=[],
            reason_codes=[],
            blocked_tools=[],
            allowed_next_route="IntentRouter",
            audit_required=False,
        )

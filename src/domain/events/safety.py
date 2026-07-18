from __future__ import annotations

from typing import Any, Literal

from domain.events.base import ContractModel


class SafetyGuardTriggeredPayload(ContractModel):
    risk_category: str
    safety_status: Literal["warning", "blocked", "needs_clarification"]
    reasons: list[str]
    checked_action: dict[str, Any] | None = None


class SafetyActionBlockedPayload(ContractModel):
    risk_category: str
    reasons: list[str]
    blocked_action: dict[str, Any]

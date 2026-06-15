from __future__ import annotations

from application.routing.models import SafetyGateResult
from safety.engine.safety_precheck import SafetyPrecheck
from safety.engine.schemas import SafetyPrecheckInput


class SafetyGate:
    """Compatibility wrapper for routing safety checks."""

    def check(self, text: str) -> SafetyGateResult:
        result = SafetyPrecheck().check(
            SafetyPrecheckInput(
                original_text=text,
                working_text=text,
            )
        )
        if result.severity == "critical":
            return SafetyGateResult(triggered=True, reason=", ".join(result.reason_codes), severity="urgent")
        if result.severity == "high":
            return SafetyGateResult(triggered=True, reason=", ".join(result.reason_codes), severity="high")
        return SafetyGateResult(triggered=False, severity="none")

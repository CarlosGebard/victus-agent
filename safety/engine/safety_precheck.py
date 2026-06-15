from __future__ import annotations

from safety.engine.decision_resolver import resolve_decision
from safety.engine.evaluator import evaluate_rules
from safety.engine.rule_loader import load_rules
from safety.engine.schemas import SafetyPrecheckInput, SafetyPrecheckResult


class SafetyPrecheck:
    def __init__(self) -> None:
        self._rules = load_rules()

    def check(self, request: SafetyPrecheckInput) -> SafetyPrecheckResult:
        text = request.working_text or request.original_text
        signals = evaluate_rules(text, self._rules)
        return resolve_decision(signals)

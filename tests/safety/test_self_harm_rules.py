from __future__ import annotations

import json

from safety.datasets.normalize_aegis import normalize_row
from safety.engine.evaluator import evaluate_rules
from safety.engine.rule_loader import load_rules
from safety.engine.safety_precheck import SafetyPrecheck
from safety.engine.schemas import SafetyPrecheckInput


def test_rule_loader_loads_self_harm_rules() -> None:
    rules = load_rules()

    assert {rule.id for rule in rules} >= {
        "self_harm.explicit_suicidal_intent",
        "self_harm.self_harm_intent",
        "self_harm.passive_ideation",
    }


def test_phrase_and_regex_matching() -> None:
    rules = load_rules()

    phrase_signals = evaluate_rules("I want to kill myself", rules)
    regex_signals = evaluate_rules("I am going to cut myself", rules)

    assert "self_harm.explicit_suicidal_intent" in {signal.rule_id for signal in phrase_signals}
    assert "self_harm.self_harm_intent" in {signal.rule_id for signal in regex_signals}


def test_explicit_suicidal_intent_routes_to_emergency() -> None:
    result = SafetyPrecheck().check(
        SafetyPrecheckInput(
            original_text="me quiero suicidar",
            working_text="i want to kill myself",
        )
    )

    assert result.decision == "emergency_escalation"
    assert result.severity == "critical"
    assert result.categories == ["self_harm"]
    assert result.allowed_next_route == "EmergencySupportResponse"
    assert result.matched_rules == ["self_harm.explicit_suicidal_intent"]
    assert "planning" in result.blocked_tools
    assert result.audit_required is True


def test_high_risk_self_harm_routes_to_safety_triage() -> None:
    result = SafetyPrecheck().check(
        SafetyPrecheckInput(
            original_text="quiero hacerme daño",
            working_text="i am going to hurt myself",
        )
    )

    assert result.decision == "route_to_safety_triage"
    assert result.severity == "high"
    assert result.allowed_next_route == "SafetyTriageRoute"
    assert result.reason_codes == ["self_harm_intent"]


def test_hard_negative_harmless_expressions_are_allowed() -> None:
    safety = SafetyPrecheck()

    for text in ["this homework is killing me", "I'm dying of hunger"]:
        result = safety.check(
            SafetyPrecheckInput(original_text=text, working_text=text)
        )
        assert result.decision == "allow"
        assert result.categories == ["none"]


def test_positive_signal_wins_when_hard_negative_also_matches() -> None:
    text = "this homework is killing me but i want to kill myself"

    result = SafetyPrecheck().check(
        SafetyPrecheckInput(original_text=text, working_text=text)
    )

    assert result.decision == "emergency_escalation"


def test_normalize_aegis_maps_self_harm_category() -> None:
    row = {
        "prompt": "I want to kill myself",
        "violated_category": "Suicide and Self Harm",
        "unsafe": True,
    }

    normalized = normalize_row(row, {"Suicide and Self Harm": "self_harm"})

    assert normalized == {
        "source": "aegis_2_0",
        "text": "I want to kill myself",
        "category": "self_harm",
        "unsafe": True,
        "source_category": "Suicide and Self Harm",
    }

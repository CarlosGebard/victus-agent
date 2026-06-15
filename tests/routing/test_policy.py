from application.routing.models import IntentScore, SafetyGateResult
from application.routing.policy import RoutingPolicy
from application.routing.prototype_store import RouterThresholds


def _policy() -> RoutingPolicy:
    return RoutingPolicy(
        "victus-router-v1",
        RouterThresholds(
            accept_score=0.82,
            accept_margin=0.12,
            multi_score=0.75,
            multi_second_score=0.72,
            clarify_below=0.58,
        ),
    )


def _score(intent_type: str, route: str, score: float) -> IntentScore:
    return IntentScore(
        intent_type=intent_type,
        route=route,
        score=score,
        positive_score=score,
        definition_score=score,
        boundary_score=0.0,
        negative_score=0.0,
    )


def test_high_safety_overrides_scores() -> None:
    decision = _policy().decide(
        input_text="x",
        normalized_text="x",
        scores=[_score("new_plan", "PlanningSessionGraph", 0.99)],
        safety=SafetyGateResult(triggered=True, severity="high", reason="risk"),
    )
    assert decision.route == "SafetyTriageRoute"
    assert decision.decision == "safety"


def test_confident_single_intent_routes_directly() -> None:
    decision = _policy().decide(
        input_text="x",
        normalized_text="x",
        scores=[
            _score("new_plan", "PlanningSessionGraph", 0.90),
            _score("revise_plan", "PlanRevisionGraph", 0.70),
        ],
        safety=SafetyGateResult(triggered=False, severity="none"),
    )
    assert decision.route == "PlanningSessionGraph"
    assert decision.decision == "route"


def test_confident_multi_intent_goes_mixed() -> None:
    decision = _policy().decide(
        input_text="x",
        normalized_text="x",
        scores=[
            _score("new_plan", "PlanningSessionGraph", 0.80),
            _score("evidence_question", "EvidenceAnswerGraph", 0.76),
        ],
        safety=SafetyGateResult(triggered=False, severity="none"),
    )
    assert decision.route == "MixedIntentResolver"
    assert decision.decision == "mixed"
    assert decision.secondary_intents == ["evidence_question"]


def test_low_confidence_clarifies() -> None:
    decision = _policy().decide(
        input_text="x",
        normalized_text="x",
        scores=[_score("new_plan", "PlanningSessionGraph", 0.40)],
        safety=SafetyGateResult(triggered=False, severity="none"),
    )
    assert decision.route == "ClarificationRoute"
    assert decision.requires_clarification is True

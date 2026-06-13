from victus_routing.cli import domain_percentages, format_domain_percentages
from victus_routing.models import IntentScore, RouteDecision


def _score(intent_type: str, route: str, score: float) -> IntentScore:
    return IntentScore(
        intent_type=intent_type,
        route=route,
        score=score,
        positive_score=score,
        definition_score=0.0,
        boundary_score=0.0,
        negative_score=0.0,
    )


def test_domain_percentages_normalize_positive_scores() -> None:
    scores = [
        _score("new_plan", "PlanningSessionGraph", 0.75),
        _score("weekly_review", "WeeklyReviewGraph", 0.25),
        _score("evidence_question", "EvidenceAnswerGraph", -0.10),
    ]

    percentages = domain_percentages(scores)

    assert percentages[0][1] == 75.0
    assert percentages[1][1] == 25.0
    assert percentages[2][1] == 0.0


def test_format_domain_percentages_outputs_human_readable_routes() -> None:
    decision = RouteDecision(
        router_version="victus-router-v1",
        input_text="hazme un plan de comidas",
        normalized_text="hazme un plan de comidas",
        decision="route",
        route="PlanningSessionGraph",
        intent_type="new_plan",
        confidence=0.9,
        scores=[
            _score("new_plan", "PlanningSessionGraph", 0.9),
            _score("weekly_review", "WeeklyReviewGraph", 0.1),
        ],
    )

    output = format_domain_percentages(decision)

    assert "Route: PlanningSessionGraph" in output
    assert "PlanningSessionGraph / new_plan: 90.00%" in output
    assert "WeeklyReviewGraph / weekly_review: 10.00%" in output

from pathlib import Path

from victus_routing.router import IntentRouter


def test_direct_safety(router: IntentRouter) -> None:
    decision = router.route("me duele el pecho y me falta el aire")
    assert decision.route == "SafetyTriageRoute"


def test_event_capture(router: IntentRouter) -> None:
    decision = router.route("hoy comi pollo con arroz en el almuerzo")
    assert decision.route == "EventCaptureGraph"


def test_new_plan(router: IntentRouter) -> None:
    decision = router.route("hazme un plan de comidas para bajar grasa")
    assert decision.route == "PlanningSessionGraph"


def test_revise_plan(router: IntentRouter) -> None:
    decision = router.route("cambia mi plan para que sea sin lactosa")
    assert decision.route == "PlanRevisionGraph"


def test_weekly_review(router: IntentRouter) -> None:
    decision = router.route("revisemos mi semana")
    assert decision.route == "WeeklyReviewGraph"


def test_evidence(router: IntentRouter) -> None:
    decision = router.route("qué dice la evidencia sobre creatina y fuerza")
    assert decision.route == "EvidenceAnswerGraph"


def test_mixed_or_planning_for_goal_request(router: IntentRouter) -> None:
    decision = router.route("quiero bajar grasa sin perder músculo")
    assert decision.route in {"MixedIntentResolver", "PlanningSessionGraph"}


def test_medical_supplement_safety_overlay_or_triage(router: IntentRouter) -> None:
    decision = router.route("tengo presión alta y quiero tomar creatina")
    assert decision.route == "SafetyTriageRoute" or decision.requires_safety_overlay is True


def test_decisions_are_logged(router: IntentRouter, tmp_path: Path) -> None:
    router.route("revisemos mi semana")
    assert router.log_path.exists()
    assert router.log_path.read_text(encoding="utf-8").strip()

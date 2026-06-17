from __future__ import annotations

from agent.nodes.event_capture.event_mapping import EVENT_TYPE_BY_ACTION
from agent.nodes.event_capture.policy import contains_high_risk_symptom, contains_nutrition_value_key
from agent.nodes.event_capture.schemas import EventCaptureDecision, EventCaptureInput
from agent.nodes.event_capture.skill_manifest import EVENT_CAPTURE_SKILLS


class EventCaptureValidationError(ValueError):
    pass


def validate_event_capture_decision(
    decision: EventCaptureDecision,
    input: EventCaptureInput | None = None,
) -> EventCaptureDecision:
    errors: list[str] = []

    skill = EVENT_CAPTURE_SKILLS.get(decision.selected_skill)
    if skill is None:
        errors.append("selected_skill is not known")
    elif decision.capture_action not in skill["allowed_actions"]:
        errors.append("selected_skill does not allow capture_action")

    expected_event = EVENT_TYPE_BY_ACTION[decision.capture_action]
    if decision.event_type_candidate != expected_event:
        errors.append("event_type_candidate does not match capture_action")

    if decision.capture_action == "log_meal":
        items = _meal_items(decision)
        if not items or not all(isinstance(item, dict) and item.get("name") for item in items):
            errors.append("log_meal requires extracted.meal.items with item names")
        if decision.capture_entity_type != "meal":
            errors.append("log_meal must use meal entity type")

    if decision.capture_action == "edit_meal":
        if not decision.referenced_record and not decision.clarification_question:
            errors.append("edit_meal requires referenced_record or clarification_question")
        if decision.capture_entity_type != "meal":
            errors.append("edit_meal must use meal entity type")

    if decision.capture_action == "delete_meal":
        if not decision.referenced_record and not decision.clarification_question:
            errors.append("delete_meal requires referenced_record or clarification_question")
        if decision.capture_entity_type != "meal":
            errors.append("delete_meal must use meal entity type")

    if decision.capture_action == "log_biometrics":
        biometrics = _payload(decision, "biometrics")
        if not biometrics.get("metric"):
            errors.append("log_biometrics requires extracted.biometrics.metric")
        if not (
            biometrics.get("raw_value_text")
            or biometrics.get("value") is not None
            or biometrics.get("systolic") is not None
        ):
            errors.append("log_biometrics requires raw_value_text or numeric value")
        if decision.capture_entity_type != "biometrics":
            errors.append("log_biometrics must use biometrics entity type")

    if decision.capture_action == "log_lifestyle_metric":
        lifestyle = _payload(decision, "lifestyle_metric")
        if not lifestyle.get("metric"):
            errors.append("log_lifestyle_metric requires extracted.lifestyle_metric.metric")
        if decision.capture_entity_type != "lifestyle_metric":
            errors.append("log_lifestyle_metric must use lifestyle_metric entity type")

    if decision.capture_action == "log_symptom":
        symptom = _payload(decision, "symptom")
        if not symptom.get("raw_text") and not symptom.get("category"):
            errors.append("log_symptom requires extracted.symptom.raw_text or category")
        if decision.capture_entity_type != "symptom":
            errors.append("log_symptom must use symptom entity type")

    if decision.capture_action == "needs_clarification":
        if decision.selected_skill != "clarification.request":
            errors.append("needs_clarification must use clarification.request")
        if not decision.clarification_question:
            errors.append("needs_clarification requires clarification_question")

    if decision.capture_action == "reroute":
        if decision.selected_skill != "none":
            errors.append("reroute must use selected_skill=none")
        if decision.event_type_candidate != "none":
            errors.append("reroute must use event_type_candidate=none")

    if contains_nutrition_value_key(decision.extracted):
        errors.append("extracted payload must not contain calories, macros, or nutrients")

    if input and contains_high_risk_symptom(input.normalized_text):
        if not decision.requires_safety_validation:
            errors.append("high-risk symptoms require safety validation")

    if errors:
        raise EventCaptureValidationError("; ".join(errors))
    return decision


def _payload(decision: EventCaptureDecision, key: str) -> dict[str, object]:
    payload = decision.extracted.get(key, {})
    return payload if isinstance(payload, dict) else {}


def _meal_items(decision: EventCaptureDecision) -> list[object]:
    meal = _payload(decision, "meal")
    items = meal.get("items", [])
    return items if isinstance(items, list) else []

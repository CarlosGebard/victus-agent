from __future__ import annotations

import re

from tools.event_capture.contract import EventCaptureDecision, EventCaptureInput


_NUTRITION_VALUE_KEYS = {
    "calories",
    "calorias",
    "calorías",
    "kcal",
    "macros",
    "protein",
    "proteina",
    "proteína",
    "carbs",
    "carbohydrates",
    "carbohidratos",
    "fat",
    "grasas",
    "nutrients",
    "nutrientes",
}


def decide_with_policy(input: EventCaptureInput, *, original_text: str = "") -> EventCaptureDecision:
    missing_fields = _missing_quantity_fields(input, original_text=original_text)
    if missing_fields:
        return _clarification(
            missing_fields=missing_fields,
            question=_quantity_question(input, missing_fields),
            occurred_at_text=input.occurred_at_text,
        )
    return _decision(
        capture_action="log_meal",
        items=input.items,
        occurred_at_text=input.occurred_at_text,
        requires_confirmation=False,
        requires_safety_validation=False,
        reason="Model supplied structured meal capture intent.",
    )


def contains_nutrition_value_key(payload: object) -> bool:
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).casefold() in _NUTRITION_VALUE_KEYS:
                return True
            if contains_nutrition_value_key(value):
                return True
    if isinstance(payload, list):
        return any(contains_nutrition_value_key(item) for item in payload)
    return False


def _decision(**kwargs: object) -> EventCaptureDecision:
    return EventCaptureDecision(**kwargs)


def _clarification(
    *, missing_fields: list[str], question: str, occurred_at_text: str
) -> EventCaptureDecision:
    return _decision(
        capture_action="needs_clarification",
        items=[],
        missing_fields=missing_fields,
        occurred_at_text=occurred_at_text,
        requires_confirmation=False,
        requires_safety_validation=False,
        clarification_question=question,
        reason="Meal quantities are required before recording.",
    )


def _missing_quantity_fields(input: EventCaptureInput, *, original_text: str = "") -> list[str]:
    missing: list[str] = []
    for index, item in enumerate(input.items):
        if item.quantity is None:
            missing.append(f"items[{index}].quantity")
        if item.unit is None:
            missing.append(f"items[{index}].unit")
        if _looks_like_inferred_single_unit(item, original_text):
            if f"items[{index}].quantity" not in missing:
                missing.append(f"items[{index}].quantity")
            if f"items[{index}].unit" not in missing:
                missing.append(f"items[{index}].unit")
    return missing


def _looks_like_inferred_single_unit(item, original_text: str) -> bool:
    if item.quantity != 1 or item.unit not in {"g", "ml"}:
        return False
    text = original_text.casefold()
    if re.search(r"\b(g|gr|gramo|gramos|ml|mililitro|mililitros)\b", text):
        return False
    name = re.escape(item.name.casefold())
    return bool(re.search(rf"\b(un|una|1)\s+{name}\b", text))


def _quantity_question(input: EventCaptureInput, missing_fields: list[str]) -> str:
    if len(input.items) == 1:
        item = input.items[0]
        if item.quantity is None and item.unit is None:
            return f"¿Qué cantidad de {item.name} consumiste en gramos o mililitros?"
        if item.quantity is None:
            return f"¿Qué cantidad de {item.name} consumiste en {item.unit}?"
        return f"¿Fue en gramos o mililitros la cantidad de {item.name}?"
    return "¿Qué cantidad consumiste de cada alimento, usando gramos o mililitros?"


class EventCapturePolicyError(ValueError):
    pass


def validate_decision(
    decision: EventCaptureDecision, input: EventCaptureInput
) -> EventCaptureDecision:
    errors: list[str] = []
    if decision.capture_action == "log_meal" and not _valid_meal(decision):
        errors.append("log_meal requires items with name, quantity, and unit")
    if decision.capture_action == "needs_clarification" and not decision.clarification_question:
        errors.append("needs_clarification requires a question")
    if contains_nutrition_value_key(decision.model_dump(mode="python")):
        errors.append("decision payload must not contain nutrition estimates")
    if errors:
        raise EventCapturePolicyError("; ".join(errors))
    return decision


def _valid_meal(decision: EventCaptureDecision) -> bool:
    return bool(decision.items) and all(
        item.name and item.quantity is not None and item.unit for item in decision.items
    )

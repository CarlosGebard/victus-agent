from __future__ import annotations

import re

from agent.nodes.event_capture.event_mapping import EVENT_TYPE_BY_ACTION
from agent.nodes.event_capture.schemas import EventCaptureDecision, EventCaptureInput


_PROFILE_REROUTE_PATTERNS = (
    r"\b(al[eé]rgic[oa]|alergia|intolerante|intolerancia|cel[ií]ac)\b",
    r"\b(no me gusta[n]?|prefiero|dislike|ll[aá]mame|me llamo|mi nombre es)\b",
    r"\b(presupuesto|horario|rutina|halal|kosher|vegan[oa]|vegetarian[oa])\b",
)
_OTHER_REROUTE_PATTERNS = (
    r"\b(plan|men[uú]|dieta|receta|meal plan|revisa mi plan|objetivo|goal)\b",
    r"\b(evidencia|estudio|paper|ciencia|cient[ií]fic|por qu[eé]|es cierto)\b",
)
_EDIT_PATTERNS = (
    r"\b(corrige|corregir|edita|editar|cambia|actualiza|modifica|no era|quise decir)\b",
)
_DELETE_PATTERNS = (
    r"\b(elimina|borra|quita|saca|remueve|delete|remove)\b",
)
_MEAL_PATTERNS = (
    r"\b(com[ií]|comer|almorc[eé]|cen[eé]|desayun[eé]|tom[eé]|beb[ií])\b",
    r"\b(desayuno|almuerzo|cena|snack|colaci[oó]n|merienda)\b",
)
_MEAL_TYPE_PATTERNS = {
    "breakfast": (r"\bdesayun", r"\bbreakfast\b"),
    "lunch": (r"\balmuer", r"\blunch\b"),
    "dinner": (r"\bcen", r"\bdinner\b"),
    "snack": (r"\bsnack\b", r"\bcolaci[oó]n\b", r"\bmerienda\b"),
}
_BIOMETRIC_PATTERNS = {
    "blood_pressure": (r"\bpresi[oó]n\b", r"\bmmhg\b", r"\b\d{2,3}/\d{2,3}\b"),
    "weight": (r"\bpeso\b", r"\bpes[eé]\b", r"\bkg\b", r"\bkilos?\b"),
    "glucose": (r"\bglucosa\b", r"\bmg/dl\b"),
    "heart_rate": (r"\bfrecuencia cardiaca\b", r"\bpulso\b", r"\blpm\b", r"\bbpm\b"),
    "body_measurement": (r"\bcintura\b", r"\bcadera\b", r"\bpecho\b", r"\bmedida\b", r"\bcm\b"),
}
_LIFESTYLE_PATTERNS = {
    "sleep_duration": (r"\bdorm[ií]\b", r"\bsue[nñ]o\b", r"\bhoras?\b"),
    "water_intake": (r"\bagua\b", r"\blitros?\b", r"\bvasos?\b"),
    "steps": (r"\bpasos\b",),
    "stress": (r"\bestr[eé]s\b", r"\bestresad[oa]\b"),
    "energy": (r"\benerg[ií]a\b", r"\bcansad[oa]\b"),
    "hunger": (r"\bhambre\b", r"\bsaciedad\b"),
}
_SYMPTOM_PATTERNS = {
    "headache": (r"\bdolor de cabeza\b", r"\bcefalea\b"),
    "nausea": (r"\bn[aá]usea\b", r"\bganas de vomitar\b"),
    "dizziness": (r"\bmareo\b", r"\bmared[oa]\b", r"\bv[eé]rtigo\b"),
    "pain": (r"\bdolor\b",),
    "discomfort": (r"\bmalestar\b", r"\bmolestia\b", r"\bme siento mal\b"),
}
_HIGH_RISK_SYMPTOM_PATTERNS = (
    r"\bdolor (?:en el )?pecho\b",
    r"\bfalta de aire\b",
    r"\bno puedo respirar\b",
    r"\bdesmay",
    r"\bpar[aá]lisis\b",
    r"\bdebilidad repentina\b",
    r"\bdolor de cabeza (?:muy )?(?:fuerte|severo|intenso)\b",
    r"\bsangrado\b",
    r"\bconvulsi[oó]n\b",
    r"\bsevero\b",
)
_SEVERITY_PATTERNS = {
    "severe": (r"\bsever[oa]\b", r"\bfuerte\b", r"\bintens[oa]\b", r"\binsoportable\b"),
    "medium": (r"\bmoderad[oa]\b", r"\bmedio\b"),
    "mild": (r"\bleve\b", r"\bsuave\b"),
}
_RELATIVE_TIME_PATTERNS = (
    r"\bhoy\b",
    r"\bayer\b",
    r"\besta ma[nñ]ana\b",
    r"\banoche\b",
    r"\bdespu[eé]s de [a-z0-9\s]+",
    r"\bantes de [a-z0-9\s]+",
)
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


def decide_with_policy(input: EventCaptureInput) -> EventCaptureDecision:
    text = _normalize(input.normalized_text)
    occurred_at_text = _extract_occurred_at_text(text)

    if _matches_any(text, _PROFILE_REROUTE_PATTERNS + _OTHER_REROUTE_PATTERNS):
        return _decision(
            capture_action="reroute",
            capture_entity_type="unknown",
            selected_skill="none",
            event_type_candidate="none",
            requires_confirmation=False,
            requires_safety_validation=False,
            occurred_at_text=occurred_at_text,
            reason="Request belongs to another Victus route.",
        )

    if _matches_any(text, _DELETE_PATTERNS):
        reference = _extract_reference(text, input.nutrition_status_digest)
        if not reference:
            return _clarification("Que comida o evento quieres eliminar?", occurred_at_text)
        return _decision(
            capture_action="delete_meal",
            capture_entity_type="meal",
            selected_skill="nutrition.delete_meal",
            event_type_candidate="meal.deleted",
            referenced_record=reference,
            occurred_at_text=occurred_at_text,
            requires_confirmation=False if _is_explicit_delete(text) else True,
            requires_safety_validation=False,
            reason="User requested deletion of a resolvable meal record.",
        )

    if _matches_any(text, _EDIT_PATTERNS):
        reference = _extract_reference(text, input.nutrition_status_digest)
        if not reference:
            return _clarification("Que comida registrada quieres corregir?", occurred_at_text)
        return _decision(
            capture_action="edit_meal",
            capture_entity_type="meal",
            selected_skill="nutrition.edit_meal",
            event_type_candidate="meal.edited",
            extracted=_meal_extracted(text),
            referenced_record=reference,
            occurred_at_text=occurred_at_text,
            requires_confirmation=False,
            requires_safety_validation=False,
            reason="User corrected a resolvable meal record.",
        )

    high_risk_symptom = contains_high_risk_symptom(text)
    symptom_category = _matched_key(text, _SYMPTOM_PATTERNS)
    if high_risk_symptom or symptom_category:
        return _decision(
            capture_action="log_symptom",
            capture_entity_type="symptom",
            selected_skill="symptom.log",
            event_type_candidate="symptom.logged",
            extracted=_symptom_extracted(text, symptom_category or "other"),
            occurred_at_text=occurred_at_text,
            requires_confirmation=False,
            requires_safety_validation=high_risk_symptom,
            reason="User reported a physical symptom.",
        )

    biometric_metric = _matched_key(text, _BIOMETRIC_PATTERNS)
    if biometric_metric:
        extracted = _biometrics_extracted(text, biometric_metric)
        if not _has_biometric_value(extracted):
            return _clarification("Que valor exacto quieres registrar?", occurred_at_text)
        return _decision(
            capture_action="log_biometrics",
            capture_entity_type="biometrics",
            selected_skill="biometrics.log",
            event_type_candidate="biometrics.logged",
            extracted=extracted,
            occurred_at_text=occurred_at_text,
            requires_confirmation=False,
            requires_safety_validation=False,
            reason="User reported an explicit biometric value.",
        )

    lifestyle_metric = _matched_key(text, _LIFESTYLE_PATTERNS)
    if lifestyle_metric:
        extracted = _lifestyle_extracted(text, lifestyle_metric)
        return _decision(
            capture_action="log_lifestyle_metric",
            capture_entity_type="lifestyle_metric",
            selected_skill="lifestyle.log",
            event_type_candidate="lifestyle_metric.logged",
            extracted=extracted,
            occurred_at_text=occurred_at_text,
            requires_confirmation=False,
            requires_safety_validation=False,
            reason="User reported a lifestyle metric.",
        )

    if _matches_any(text, _MEAL_PATTERNS):
        extracted = _meal_extracted(text)
        if not extracted["meal"]["items"]:
            return _clarification("Que alimento o bebida quieres registrar?", occurred_at_text)
        return _decision(
            capture_action="log_meal",
            capture_entity_type="meal",
            selected_skill="nutrition.log_meal",
            event_type_candidate="meal.logged",
            extracted=extracted,
            occurred_at_text=occurred_at_text,
            requires_confirmation=False,
            requires_safety_validation=False,
            reason="User reported explicit food or drink intake.",
        )

    return _decision(
        capture_action="reroute",
        capture_entity_type="unknown",
        selected_skill="none",
        event_type_candidate="none",
        requires_confirmation=False,
        requires_safety_validation=False,
        occurred_at_text=occurred_at_text,
        reason="No fast-changing personal data capture was detected.",
    )


def contains_high_risk_symptom(text: str) -> bool:
    return _matches_any(_normalize(text), _HIGH_RISK_SYMPTOM_PATTERNS)


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


def _meal_extracted(text: str) -> dict[str, object]:
    item_text = _extract_after_meal_verb(text)
    items = []
    for raw_item in re.split(r",|\by\b|\bcon\b|\+", item_text):
        item = _remove_relative_time(raw_item.strip(" .,:;"))
        if not item or item in {"hoy", "ayer", "esta manana", "esta mañana"}:
            continue
        quantity_text = _extract_quantity_text(item)
        name = item
        if quantity_text:
            name = item.replace(quantity_text, "").strip(" de ")
        items.append(
            {
                "name": name,
                **({"quantity_text": quantity_text} if quantity_text else {}),
            }
        )
    return {"meal": {"meal_type": _meal_type(text), "items": items}}


def _biometrics_extracted(text: str, metric: str) -> dict[str, object]:
    if metric == "blood_pressure":
        match = re.search(r"\b(\d{2,3})/(\d{2,3})\b", text)
        if match:
            raw = match.group(0)
            return {
                "biometrics": {
                    "metric": "blood_pressure",
                    "systolic": int(match.group(1)),
                    "diastolic": int(match.group(2)),
                    "unit": "mmHg",
                    "raw_value_text": raw,
                }
            }
    value, unit, raw = _extract_number_unit(text)
    payload: dict[str, object] = {"metric": metric}
    if value is not None:
        payload["value"] = value
    if unit:
        payload["unit"] = unit
    if raw:
        payload["raw_value_text"] = raw
    return {"biometrics": payload}


def _lifestyle_extracted(text: str, metric: str) -> dict[str, object]:
    value, unit, raw = _extract_number_unit(text)
    payload: dict[str, object] = {"metric": metric}
    if value is not None:
        payload["value"] = value
    if unit:
        payload["unit"] = unit
    if raw:
        payload["raw_value_text"] = raw
    qualitative = _extract_qualitative_value(text)
    if qualitative and "value" not in payload:
        payload["value"] = qualitative
        payload["raw_value_text"] = qualitative
    return {"lifestyle_metric": payload}


def _symptom_extracted(text: str, category: str) -> dict[str, object]:
    return {
        "symptom": {
            "category": category,
            "severity": _severity(text),
            **({"body_location": _body_location(text)} if _body_location(text) else {}),
            **({"context": _context(text)} if _context(text) else {}),
            "raw_text": text,
        }
    }


def _has_biometric_value(extracted: dict[str, object]) -> bool:
    payload = extracted.get("biometrics", {})
    return isinstance(payload, dict) and (
        "raw_value_text" in payload or "value" in payload or "systolic" in payload
    )


def _extract_number_unit(text: str) -> tuple[float | int | None, str | None, str | None]:
    match = re.search(
        r"\b(\d+(?:[.,]\d+)?)\s*(kg|kilos?|mmhg|mg/dl|bpm|lpm|cm|litros?|vasos?|horas?|pasos)?\b",
        text,
    )
    if not match:
        return None, None, None
    raw = match.group(0)
    number_text = match.group(1).replace(",", ".")
    value = float(number_text) if "." in number_text else int(number_text)
    unit = _normalize_unit(match.group(2))
    return value, unit, raw


def _extract_quantity_text(text: str) -> str | None:
    match = re.search(r"\b\d+(?:[.,]\d+)?\s*(g|gr|gramos?|kg|ml|l|tazas?|cucharadas?)\b", text)
    return match.group(0) if match else None


def _extract_after_meal_verb(text: str) -> str:
    match = re.search(
        r"(?:com[ií]|almorc[eé]|cen[eé]|desayun[eé]|tom[eé]|beb[ií]|snack de|colaci[oó]n de)\s+(.+)$",
        text,
    )
    if match:
        return match.group(1)
    return text


def _extract_reference(text: str, digest: str | None) -> str | None:
    match = re.search(r"\b(meal_[a-z0-9_-]+|evento_[a-z0-9_-]+|registro_[a-z0-9_-]+)\b", text)
    if match:
        return match.group(1)
    if re.search(r"\b(ultima|[uú]ltima|ultimo|[uú]ltimo|anterior)\b", text) and digest:
        return "latest_from_context"
    return None


def _extract_occurred_at_text(text: str) -> str | None:
    for pattern in _RELATIVE_TIME_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def _remove_relative_time(text: str) -> str:
    cleaned = text
    for pattern in _RELATIVE_TIME_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned).strip(" .,:;")
    return cleaned


def _meal_type(text: str) -> str:
    for meal_type, patterns in _MEAL_TYPE_PATTERNS.items():
        if _matches_any(text, patterns):
            return meal_type
    return "unknown"


def _severity(text: str) -> str:
    for severity, patterns in _SEVERITY_PATTERNS.items():
        if _matches_any(text, patterns):
            return severity
    return "unknown"


def _body_location(text: str) -> str | None:
    locations = {
        "head": (r"\bcabeza\b",),
        "chest": (r"\bpecho\b",),
        "stomach": (r"\best[oó]mago\b", r"\bguata\b", r"\babdomen\b"),
        "back": (r"\bespalda\b",),
        "leg": (r"\bpierna\b",),
        "arm": (r"\bbrazo\b",),
    }
    return _matched_key(text, locations)


def _context(text: str) -> str | None:
    match = re.search(r"\b(despu[eé]s de .+|antes de .+)$", text)
    return match.group(1) if match else None


def _extract_qualitative_value(text: str) -> str | None:
    match = re.search(r"\b(alto|alta|medio|media|bajo|baja|leve|moderado|severo|mucha|poca)\b", text)
    return match.group(1) if match else None


def _normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    unit = unit.casefold()
    return {
        "kilo": "kg",
        "kilos": "kg",
        "litro": "liters",
        "litros": "liters",
        "hora": "hours",
        "horas": "hours",
        "vaso": "glasses",
        "vasos": "glasses",
    }.get(unit, unit)


def _matched_key(text: str, pattern_by_key: dict[str, tuple[str, ...]]) -> str | None:
    for key, patterns in pattern_by_key.items():
        if _matches_any(text, patterns):
            return key
    return None


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _is_explicit_delete(text: str) -> bool:
    return bool(re.search(r"\b(elimina|borra|delete)\b", text))


def _clarification(question: str, occurred_at_text: str | None) -> EventCaptureDecision:
    return _decision(
        capture_action="needs_clarification",
        capture_entity_type="unknown",
        selected_skill="clarification.request",
        event_type_candidate="none",
        occurred_at_text=occurred_at_text,
        requires_confirmation=False,
        requires_safety_validation=False,
        clarification_question=question,
        reason="A safe event write requires clarification.",
    )


def _decision(**kwargs: object) -> EventCaptureDecision:
    return EventCaptureDecision(**kwargs)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())

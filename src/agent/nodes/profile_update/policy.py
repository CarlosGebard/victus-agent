from __future__ import annotations

import re

from agent.nodes.profile_update.event_mapping import event_type_for_decision
from agent.nodes.profile_update.schemas import ProfileUpdateDecision, ProfileUpdateInput


_REROUTE_PATTERNS = (
    r"\b(com[ií]|almorc[eé]|cen[eé]|desayun[eé]|snack|colaci[oó]n|calor[ií]as)\b",
    r"\b(peso|glucosa|presi[oó]n|colesterol|triglic[eé]ridos|pasos|sue[nñ]o)\b",
    r"\b(me duele|dolor|s[ií]ntoma|vomit|diarrea|fiebre|mareo|n[aá]usea)\b",
    r"\b(plan|men[uú]|dieta|receta|meal plan|revisa mi plan|cambia mi goal|objetivo)\b",
    r"\b(evidencia|estudio|paper|ciencia|cient[ií]fic|por qu[eé]|es cierto)\b",
)
_ALLERGY_PATTERNS = (r"\bal[eé]rgic[oa]\b", r"\balergia\b", r"\ballergic\b", r"\ballergy\b")
_INTOLERANCE_PATTERNS = (r"\bintolerante\b", r"\bintolerancia\b", r"\bintoleran[ct]e\b")
_MEDICAL_PATTERNS = (
    r"\b(cel[ií]ac|diabetes|hipertensi[oó]n|renal|ri[nñ][oó]n|embaraz|m[eé]dic[oa])\b",
    r"\b(prescripci[oó]n|diagnosticad[oa]|doctor|doctora|nutri[oó]logo|cardi[oó]logo)\b",
)
_RELIGIOUS_PATTERNS = (r"\bhalal\b", r"\bkosher\b", r"\bpor religi[oó]n\b")
_ETHICAL_PATTERNS = (r"\bvegan[oa]\b", r"\bvegetarian[oa]\b", r"\bpor [eé]tica\b")
_AMBIGUOUS_MEDICAL_PATTERNS = (
    r"\bme cae mal\b",
    r"\bme hace mal\b",
    r"\bno me sienta bien\b",
    r"\bme hincha\b",
)
_REMOVE_PATTERNS = (
    r"\b(quita|elimina|borra|saca|remueve|remove|delete)\b",
    r"\bya no\b.*\b(alerg|intoler|restric|evit)\b",
    r"\bpuedo comer\b",
)
_WEAKEN_PATTERNS = (r"\bya no es tan grave\b", r"\bsolo un poco\b", r"\bpuedo comer un poco\b")
_DISLIKE_PATTERNS = (r"\bno me gusta[n]?\b", r"\bodio\b", r"\bdetesto\b", r"\bdislike\b")
_PREFER_PATTERNS = (r"\bprefiero\b", r"\bme gusta[n]?\b", r"\bpreferir[ií]a\b", r"\bprefer\b")
_BUDGET_PATTERNS = (r"\bpresupuesto\b", r"\bbarat[oa]\b", r"\becon[oó]mic[oa]\b", r"\bcar[oa]\b")
_SCHEDULE_PATTERNS = (r"\bhorario\b", r"\brutina\b", r"\bdesayuno a las\b", r"\bceno a las\b")
_COOKING_PATTERNS = (r"\bcocina\b", r"\bcocinar\b", r"\bpreparaci[oó]n\b", r"\br[aá]pid[oa]\b")
_IDENTITY_PATTERNS = (
    r"\bll[aá]mame\b",
    r"\bme llamo\b",
    r"\bmi nombre es\b",
    r"\bprefiero que me digas\b",
    r"\bcall me\b",
)


def decide_with_policy(input: ProfileUpdateInput) -> ProfileUpdateDecision:
    text = _normalize(input.normalized_text)

    if _matches_any(text, _REROUTE_PATTERNS):
        return _decision(
            profile_action="reroute",
            profile_entity_type="unknown",
            selected_skill="none",
            requires_confirmation=False,
            requires_safety_validation=False,
            event_type_candidate="none",
            reason="Request belongs to another Victus route, not durable profile update.",
        )

    target = _extract_target(text)
    is_remove = _matches_any(text, _REMOVE_PATTERNS)
    is_weaken = _matches_any(text, _WEAKEN_PATTERNS)

    if _matches_any(text, _AMBIGUOUS_MEDICAL_PATTERNS):
        return _decision(
            profile_action="needs_clarification",
            profile_entity_type="unknown",
            selected_skill="clarification.request",
            target=target,
            requires_confirmation=False,
            requires_safety_validation=True,
            clarification_question=(
                "Quieres que lo registre como intolerancia/restriccion, o solo como una "
                "preferencia para evitarlo?"
            ),
            event_type_candidate="none",
            reason="Medical or intolerance meaning is ambiguous.",
        )

    restriction_kind = _restriction_kind(text)
    if restriction_kind != "not_applicable":
        if is_remove or is_weaken:
            action = "remove_restriction" if is_remove else "update_restriction"
            return _restriction_decision(
                action=action,
                target=target,
                restriction_kind=restriction_kind,
                requires_confirmation=restriction_kind in {"allergy", "medical_restriction"},
                reason="User is removing or weakening an existing safety-relevant restriction.",
            )
        return _restriction_decision(
            action="add_restriction",
            target=target,
            restriction_kind=restriction_kind,
            requires_confirmation=False,
            reason="User explicitly declared a durable restriction.",
        )

    if is_remove:
        return _decision(
            profile_action="remove_preference",
            profile_entity_type="preference",
            selected_skill="profile.remove_preference",
            target=target,
            category=None if target else "preference",
            direction="remove",
            requires_confirmation=False,
            requires_safety_validation=False,
            event_type_candidate="preference.removed",
            reason="User is removing a non-safety profile preference.",
        )

    if _matches_any(text, _IDENTITY_PATTERNS):
        return _preference_decision(
            text=text,
            target=_extract_identity_target(text) or target,
            entity_type="identity_preference",
            category="display_name",
            direction="prefer",
            reason="User changed how they want to be addressed.",
        )

    if _matches_any(text, _DISLIKE_PATTERNS):
        return _preference_decision(
            text=text,
            target=target,
            entity_type="preference",
            category=None if target else "food_dislike",
            direction="dislike",
            reason="User expressed a durable dislike.",
        )

    if _matches_any(text, _PREFER_PATTERNS):
        entity_type = _preference_entity_type(text)
        return _preference_decision(
            text=text,
            target=target,
            entity_type=entity_type,
            category=_category_for_entity(entity_type),
            direction="prefer",
            reason="User expressed a durable preference.",
        )

    if _matches_any(text, _BUDGET_PATTERNS):
        return _preference_decision(
            text=text,
            target=target,
            entity_type="budget_preference",
            category="budget",
            direction="limit",
            reason="User changed a budget preference.",
        )

    if _matches_any(text, _SCHEDULE_PATTERNS):
        return _preference_decision(
            text=text,
            target=target,
            entity_type="schedule_preference",
            category="schedule",
            direction="prefer",
            reason="User changed a stable schedule preference.",
        )

    if _matches_any(text, _COOKING_PATTERNS):
        return _preference_decision(
            text=text,
            target=target,
            entity_type="cooking_preference",
            category="cooking_style",
            direction="prefer",
            reason="User changed a cooking preference.",
        )

    return _decision(
        profile_action="reroute",
        profile_entity_type="unknown",
        selected_skill="none",
        requires_confirmation=False,
        requires_safety_validation=False,
        event_type_candidate="none",
        reason="No durable profile update was detected.",
    )


def contains_explicit_allergy(text: str) -> bool:
    return _matches_any(_normalize(text), _ALLERGY_PATTERNS)


def contains_explicit_medical_restriction(text: str) -> bool:
    return _matches_any(_normalize(text), _MEDICAL_PATTERNS)


def _restriction_decision(
    *,
    action: str,
    target: str | None,
    restriction_kind: str,
    requires_confirmation: bool,
    reason: str,
) -> ProfileUpdateDecision:
    severity = {
        "allergy": "high",
        "intolerance": "medium",
        "medical_restriction": "high",
    }.get(restriction_kind, "medium")
    safety = restriction_kind in {"allergy", "medical_restriction"} or (
        restriction_kind == "intolerance" and severity in {"high", "critical"}
    )
    skill = f"profile.{action.removesuffix('_restriction')}_restriction"
    decision = _decision(
        profile_action=action,
        profile_entity_type="restriction",
        selected_skill=skill,
        target=target,
        direction="avoid" if action == "add_restriction" else "remove",
        strength="hard" if restriction_kind in {"allergy", "medical_restriction"} else "medium",
        restriction_kind=restriction_kind,
        severity=severity,
        requires_confirmation=requires_confirmation,
        requires_safety_validation=safety,
        reason=reason,
    )
    decision.event_type_candidate = event_type_for_decision(decision)
    return decision


def _preference_decision(
    *,
    text: str,
    target: str | None,
    entity_type: str,
    category: str | None,
    direction: str,
    reason: str,
) -> ProfileUpdateDecision:
    decision = _decision(
        profile_action="update_preference",
        profile_entity_type=entity_type,
        selected_skill="profile.update_preference",
        target=target,
        category=category,
        direction=direction,
        strength="medium",
        requires_confirmation=False,
        requires_safety_validation=False,
        reason=reason,
    )
    decision.event_type_candidate = event_type_for_decision(decision)
    return decision


def _decision(**kwargs: object) -> ProfileUpdateDecision:
    return ProfileUpdateDecision(**kwargs)


def _restriction_kind(text: str) -> str:
    if _matches_any(text, _ALLERGY_PATTERNS):
        return "allergy"
    if _matches_any(text, _INTOLERANCE_PATTERNS):
        return "intolerance"
    if _matches_any(text, _MEDICAL_PATTERNS):
        return "medical_restriction"
    if _matches_any(text, _RELIGIOUS_PATTERNS):
        return "religious_restriction"
    if _matches_any(text, _ETHICAL_PATTERNS):
        return "ethical_restriction"
    return "not_applicable"


def _preference_entity_type(text: str) -> str:
    if _matches_any(text, _BUDGET_PATTERNS):
        return "budget_preference"
    if _matches_any(text, _SCHEDULE_PATTERNS):
        return "schedule_preference"
    if _matches_any(text, _COOKING_PATTERNS):
        return "cooking_preference"
    return "preference"


def _category_for_entity(entity_type: str) -> str | None:
    return {
        "budget_preference": "budget",
        "schedule_preference": "schedule",
        "cooking_preference": "cooking_style",
    }.get(entity_type)


def _extract_target(text: str) -> str | None:
    patterns = (
        r"(?:al[eé]rgic[oa]\s+(?:a|al)|intolerante\s+(?:a|al))\s+(.+)$",
        r"(?:a|alergia a|intolerante a|intolerancia a|evitar|evito|sin|no me gusta[n]?|prefiero|quita|elimina|ll[aá]mame|me llamo|mi nombre es|me digas)\s+(.+)$",
        r"(?:presupuesto|horario|rutina|cocina)\s+(?:es|de|para|a)?\s*(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            target = match.group(1).strip(" .,:;")
            return target or None
    return None


def _extract_identity_target(text: str) -> str | None:
    match = re.search(r"(?:ll[aá]mame|me llamo|mi nombre es|me digas)\s+(.+)$", text)
    if not match:
        return None
    return match.group(1).strip(" .,:;") or None


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().strip().split())

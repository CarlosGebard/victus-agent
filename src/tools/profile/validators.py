from __future__ import annotations

from tools.profile.contract import ProfileUpdateDecision, ProfileUpdateInput
from tools.profile.policy import (
    contains_explicit_allergy,
    contains_explicit_medical_restriction,
)


class ProfileUpdateValidationError(ValueError):
    pass


def validate_profile_update_decision(
    decision: ProfileUpdateDecision,
    input: ProfileUpdateInput | None = None,
) -> ProfileUpdateDecision:
    errors: list[str] = []

    if input and contains_explicit_allergy(input.normalized_text):
        if decision.restriction_kind != "allergy" or decision.profile_entity_type != "restriction":
            errors.append("explicit allergies must be classified as allergy restrictions")
    if input and contains_explicit_medical_restriction(input.normalized_text):
        if (
            decision.restriction_kind != "medical_restriction"
            or decision.profile_entity_type != "restriction"
        ):
            errors.append("explicit medical restrictions must be classified as restrictions")

    if decision.profile_action in {
        "add_restriction",
        "update_restriction",
        "remove_restriction",
    }:
        if not decision.target:
            errors.append("restriction actions must include target")
        if decision.profile_entity_type != "restriction":
            errors.append("restriction actions must use restriction entity type")

    if decision.profile_action in {"update_preference", "remove_preference"}:
        if not decision.target and not decision.category:
            errors.append("preference actions must include target or category")

    if decision.profile_action == "needs_clarification":
        if not decision.clarification_question:
            errors.append("needs_clarification must include clarification_question")

    if decision.restriction_kind == "allergy" and not decision.requires_safety_validation:
        errors.append("allergy restrictions require safety validation")

    if (
        decision.profile_action == "remove_restriction"
        and decision.restriction_kind in {"allergy", "medical_restriction"}
        and (not decision.requires_confirmation or not decision.requires_safety_validation)
    ):
        errors.append("removing allergy or medical restriction requires confirmation and safety")

    if errors:
        raise ProfileUpdateValidationError("; ".join(errors))
    return decision

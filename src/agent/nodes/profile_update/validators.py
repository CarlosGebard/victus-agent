from __future__ import annotations

from agent.nodes.profile_update.event_mapping import event_type_for_decision
from agent.nodes.profile_update.policy import (
    contains_explicit_allergy,
    contains_explicit_medical_restriction,
)
from agent.nodes.profile_update.schemas import ProfileUpdateDecision, ProfileUpdateInput
from agent.nodes.profile_update.skill_manifest import PROFILE_UPDATE_SKILLS


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

    skill = PROFILE_UPDATE_SKILLS.get(decision.selected_skill)
    if skill is None:
        errors.append("selected_skill is not known")
    elif decision.profile_action not in skill["allowed_actions"]:
        errors.append("selected_skill does not allow profile_action")

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
        if decision.selected_skill != "clarification.request":
            errors.append("needs_clarification must use clarification.request")
        if not decision.clarification_question:
            errors.append("needs_clarification must include clarification_question")

    if decision.profile_action == "reroute":
        if decision.selected_skill != "none":
            errors.append("reroute must use selected_skill=none")
        if decision.event_type_candidate != "none":
            errors.append("reroute must use event_type_candidate=none")

    if decision.restriction_kind == "allergy" and not decision.requires_safety_validation:
        errors.append("allergy restrictions require safety validation")

    if (
        decision.profile_action == "remove_restriction"
        and decision.restriction_kind in {"allergy", "medical_restriction"}
        and (not decision.requires_confirmation or not decision.requires_safety_validation)
    ):
        errors.append("removing allergy or medical restriction requires confirmation and safety")

    expected_event = event_type_for_decision(decision)
    if decision.event_type_candidate != expected_event:
        errors.append("event_type_candidate does not match action and entity type")

    if errors:
        raise ProfileUpdateValidationError("; ".join(errors))
    return decision

from __future__ import annotations

from domain.events.envelope import EventActor, EventMetadata, UserEventEnvelope
from domain.events.profile import RestrictionAddedPayload
from tools.profile.contract import ProfileUpdateDecision, ProfileUpdateInput
from tools.profile.actions._common import (
    clean_leading_article,
    new_event_id,
    new_prefixed_id,
    now_iso,
)


def build_add_restriction_event(
    *,
    decision: ProfileUpdateDecision,
    input: ProfileUpdateInput,
) -> UserEventEnvelope:
    restriction_id = new_prefixed_id("restriction")
    now = now_iso()
    payload = RestrictionAddedPayload(
        restriction_id=restriction_id,
        restriction_kind=_contract_restriction_kind(decision.restriction_kind),
        condition_label=_condition_label(decision.restriction_kind),
        restricted_substance_label=clean_leading_article(decision.target),
        severity=_contract_severity(decision.severity),
        scope=_contract_scope(decision.restriction_kind),
        evidence_level="declared",
    )
    return UserEventEnvelope(
        event_id=new_event_id(),
        event_seq=0,
        user_id=input.user_id,
        event_type="restriction.added",
        aggregate_type="restriction",
        aggregate_id=restriction_id,
        occurred_at=now,
        recorded_at=now,
        source="user",
        actor=EventActor(actor_type="tool", actor_id="profile.add_restriction"),
        idempotency_key=(
            f"profile.add_restriction:{input.user_id}:{decision.target}:"
            f"{decision.restriction_kind}"
        ),
        payload=payload,
        metadata=EventMetadata(
            tool_name="profile_update",
            safety_status="blocked" if decision.requires_safety_validation else "ok",
        ),
    )


def _contract_restriction_kind(kind: str) -> str:
    return {
        "allergy": "allergy",
        "intolerance": "intolerance",
        "medical_restriction": "medical",
        "religious_restriction": "religious",
        "ethical_restriction": "advisory",
        "personal_avoidance": "advisory",
        "unknown": "unknown",
        "not_applicable": "unknown",
    }.get(kind, "unknown")


def _contract_scope(kind: str) -> str:
    if kind in {"allergy", "medical_restriction"}:
        return "absolute"
    if kind in {"intolerance", "religious_restriction", "ethical_restriction"}:
        return "dietary"
    if kind == "personal_avoidance":
        return "advisory"
    return "unknown"


def _contract_severity(severity: str) -> str:
    return {
        "critical": "high",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "unknown": "unknown",
    }.get(severity, "unknown")


def _condition_label(kind: str) -> str | None:
    return {
        "allergy": "allergy",
        "intolerance": "intolerance",
        "medical_restriction": "medical_restriction",
    }.get(kind)

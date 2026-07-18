from __future__ import annotations

from domain.events.envelope import UserEventEnvelope
from domain.projections.models.constraint import (
    ConstraintProjection,
    HardConstraint,
    SafetyFlag,
    SoftConstraint,
)
from domain.projections.projectors._common import now_iso, payload_dict

CONSTRAINT_PROJECTOR = "constraint"


def apply_constraint_event(
    projection: ConstraintProjection | None,
    event: UserEventEnvelope,
) -> ConstraintProjection:
    current = projection or ConstraintProjection(
        user_id=event.user_id,
        derived_from_event_seq=0,
        updated_at=now_iso(),
    )
    payload = payload_dict(event)
    if event.event_type == "restriction.added":
        kind = payload["restriction_kind"]
        constraint = HardConstraint(
            constraint_id=payload["restriction_id"],
            kind=kind if kind in {"allergy", "medical", "religious"} else "safety",
            label=payload["restricted_substance_label"],
            severity=payload["severity"],
            rule={
                "scope": payload["scope"],
                "evidence_level": payload["evidence_level"],
                "condition_label": payload.get("condition_label"),
            },
        )
        current.hard_constraints = [
            item for item in current.hard_constraints if item.constraint_id != constraint.constraint_id
        ]
        current.hard_constraints.append(constraint)
    elif event.event_type == "preference.updated":
        constraint = SoftConstraint(
            constraint_id=payload["preference_id"],
            kind=_soft_constraint_kind(payload["category"]),
            label=payload["item_label"],
            strength=payload["strength"],
            rule={"preference": payload["preference"], "category": payload["category"]},
        )
        current.soft_constraints = [
            item for item in current.soft_constraints if item.constraint_id != constraint.constraint_id
        ]
        current.soft_constraints.append(constraint)
    elif event.event_type in {"safety.guard_triggered", "safety.action_blocked"}:
        flag = SafetyFlag(
            flag_id=f"{event.event_type}:{event.event_seq}",
            risk_category=payload["risk_category"],
            status=payload.get("safety_status", "blocked"),
            reasons=payload["reasons"],
        )
        current.safety_flags.insert(0, flag)
        current.safety_flags = current.safety_flags[:50]

    current.derived_from_event_seq = max(current.derived_from_event_seq, event.event_seq)
    current.updated_at = now_iso()
    return current


def _soft_constraint_kind(category: str) -> str:
    if category in {"budget", "schedule", "cooking"}:
        return category
    return "preference"

from __future__ import annotations

from typing import Any, Literal

from domain.events.base import ContractModel, Severity


class RestrictionAddedPayload(ContractModel):
    restriction_id: str
    restriction_kind: Literal["medical", "religious", "allergy", "intolerance", "advisory", "unknown"]
    condition_label: str | None = None
    restricted_substance_label: str
    severity: Severity
    scope: Literal["absolute", "dietary", "advisory", "unknown"]
    evidence_level: Literal["declared", "clinical", "unknown"]


class RestrictionUpdatedPayload(ContractModel):
    restriction_id: str
    patch: dict[str, Any]
    reason: str | None = None


class PreferenceUpdatedPayload(ContractModel):
    preference_id: str
    category: Literal["food", "cuisine", "budget", "time", "schedule", "cooking", "other"]
    item_label: str
    preference: Literal["like", "neutral", "dislike"]
    strength: float
    reason: str | None = None

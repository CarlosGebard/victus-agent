from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from domain.events.base import Severity
from domain.projections.models.base import ContractModel


class RestrictionView(ContractModel):
    restriction_id: str
    kind: str
    label: str
    severity: Severity
    metadata: dict[str, Any] = Field(default_factory=dict)


class PreferenceView(ContractModel):
    preference_id: str
    category: str
    item_label: str
    preference: Literal["like", "neutral", "dislike"]
    strength: float


class UserProfileBody(ContractModel):
    display_name: str | None = None
    locale: str | None = None
    timezone: str | None = None
    age_range: str | None = None
    sex_label: str | None = None
    activity_context: str | None = None


class UserProfileProjection(ContractModel):
    user_id: str
    profile: UserProfileBody = Field(default_factory=UserProfileBody)
    restrictions: list[RestrictionView] = Field(default_factory=list)
    preferences: list[PreferenceView] = Field(default_factory=list)
    active_goal_id: str | None = None
    last_event_seq: int
    updated_at: str

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EventMealItemInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        min_length=1,
        description=(
            "Canonical food or beverage label from the user's words. Use this field, not "
            "food_label."
        ),
    )
    quantity: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Required numeric amount in the stated unit. Use null when the user did not explicitly "
            "provide an amount in grams or milliliters; never infer 1 from phrases like one item, "
            "a chicken, a serving, or a portion."
        ),
    )
    unit: Literal["g", "ml"] | None = Field(
        default=None,
        description=(
            "Required measurement unit for nutrition calculation. Use only g or ml when explicitly "
            "stated by the user. Use null when the user did not state grams or milliliters."
        ),
    )


class EventCaptureInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[EventMealItemInput] = Field(
        min_length=1,
        description="Foods or beverages consumed. Each item requires its name.",
    )
    occurred_at_text: str = Field(
        default="today",
        min_length=1,
        description="When the food was consumed; defaults to today when not explicitly provided.",
    )


class EventCaptureDecision(BaseModel):
    capture_action: Literal["log_meal", "needs_clarification"]

    items: list[EventMealItemInput] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    occurred_at_text: str | None = None

    requires_confirmation: bool
    requires_safety_validation: bool

    clarification_question: str | None = None
    reason: str = Field(min_length=1)

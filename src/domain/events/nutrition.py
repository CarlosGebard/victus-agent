from __future__ import annotations

from typing import Any, Literal

from domain.events.base import ContractModel

MealType = Literal["breakfast", "lunch", "dinner", "snack", "unknown"]
MealSource = Literal["manual", "voice", "import"]
QuantityUnit = Literal["g", "ml", "unit", "serving", "cup", "tbsp", "tsp", "unknown"]


class Quantity(ContractModel):
    value: float
    unit: QuantityUnit


class MealItem(ContractModel):
    item_id: str
    food_label: str
    quantity: Quantity | None = None
    notes: str | None = None


class MealLoggedPayload(ContractModel):
    meal_id: str
    meal_type: MealType
    consumed_at: str
    source: MealSource
    items: list[MealItem]
    notes: str | None = None


class MealEditedPayload(ContractModel):
    meal_id: str
    reason: str | None = None
    patch: dict[str, Any]


class MealDeletedPayload(ContractModel):
    meal_id: str
    reason: str | None = None
    user_confirmed: Literal[True]

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

SafetyStatus = Literal["ok", "warning", "blocked", "needs_clarification"]

EventSource = Literal["user", "system", "import", "migration", "test"]
ActorType = Literal["user", "assistant", "system", "tool"]
Severity = Literal["low", "medium", "high", "unknown"]


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

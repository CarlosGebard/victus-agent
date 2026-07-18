from __future__ import annotations

from domain.events.base import ContractModel


class ToolEventRef(ContractModel):
    event_id: str
    event_type: str
    seq: int

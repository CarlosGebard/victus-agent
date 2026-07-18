from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from domain.events.envelope import UserEventEnvelope


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def payload_dict(event: UserEventEnvelope) -> dict[str, Any]:
    payload = event.payload
    if hasattr(payload, "model_dump"):
        return payload.model_dump(mode="python", exclude_none=True)
    return dict(payload)

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from domain.events.envelope import EventActor, EventMetadata, UserEventEnvelope


def new_event_id() -> str:
    return str(uuid4())


def new_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def tool_event_envelope(
    *,
    user_id: str,
    tool_name: str,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    actor_id: str,
    payload: object,
    idempotency_key: str,
    occurred_at: str | None = None,
    safety_status: str = "ok",
) -> UserEventEnvelope:
    timestamp = occurred_at or now_iso()
    return UserEventEnvelope(
        event_id=new_event_id(),
        event_seq=0,
        user_id=user_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        occurred_at=timestamp,
        recorded_at=now_iso(),
        source="user",
        actor=EventActor(actor_type="tool", actor_id=actor_id),
        idempotency_key=idempotency_key,
        payload=payload,
        metadata=EventMetadata(tool_name=tool_name, safety_status=safety_status),
    )

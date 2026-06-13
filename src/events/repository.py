from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Connection, Select, insert, select

from db.schema import user_events
from events.models import EventActor, EventMetadata, UserEventEnvelope


class PostgresEventStore:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def append(self, event: UserEventEnvelope) -> UserEventEnvelope:
        existing = self._find_existing(event)
        if existing is not None:
            return existing

        payload = _event_to_row(event)
        payload.pop("event_seq", None)
        if payload.get("event_id") == "":
            payload.pop("event_id", None)

        row = self.connection.execute(
            insert(user_events).values(**payload).returning(user_events),
        ).mappings().one()
        return _row_to_event(dict(row))

    def list_for_user(self, user_id: str, *, after_seq: int = 0, limit: int = 100) -> list[UserEventEnvelope]:
        statement = (
            select(user_events)
            .where(user_events.c.user_id == user_id)
            .where(user_events.c.event_seq > after_seq)
            .order_by(user_events.c.event_seq)
            .limit(limit)
        )
        rows = self.connection.execute(statement).mappings().all()
        return [_row_to_event(dict(row)) for row in rows]

    def _find_existing(self, event: UserEventEnvelope) -> UserEventEnvelope | None:
        if not event.idempotency_key:
            return None
        statement: Select[Any] = select(user_events).where(
            user_events.c.user_id == event.user_id,
            user_events.c.idempotency_key == event.idempotency_key,
        )
        row = self.connection.execute(statement).mappings().first()
        return _row_to_event(dict(row)) if row else None


def _event_to_row(event: UserEventEnvelope) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "event_seq": event.event_seq,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": event.aggregate_id,
        "occurred_at": _from_iso(event.occurred_at),
        "recorded_at": _from_iso(event.recorded_at),
        "source": event.source,
        "actor": event.actor.model_dump(exclude_none=True),
        "correlation_id": event.correlation_id,
        "causation_id": event.causation_id,
        "idempotency_key": event.idempotency_key,
        "schema_version": event.schema_version,
        "payload": _dump_payload(event.payload),
        "metadata": event.metadata.model_dump(exclude_none=True),
    }


def _row_to_event(row: dict[str, Any]) -> UserEventEnvelope:
    return UserEventEnvelope(
        event_id=str(row["event_id"]),
        event_seq=int(row["event_seq"]),
        user_id=row["user_id"],
        event_type=row["event_type"],
        aggregate_type=row["aggregate_type"],
        aggregate_id=row["aggregate_id"],
        occurred_at=_to_iso(row["occurred_at"]),
        recorded_at=_to_iso(row["recorded_at"]),
        source=row["source"],
        actor=EventActor(**row["actor"]),
        correlation_id=row["correlation_id"],
        causation_id=row["causation_id"],
        idempotency_key=row["idempotency_key"],
        schema_version=row["schema_version"],
        payload=row["payload"],
        metadata=EventMetadata(**row["metadata"]),
    )


def _dump_payload(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_none=True)
    return dict(payload)


def _to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _from_iso(value: str) -> datetime | str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value

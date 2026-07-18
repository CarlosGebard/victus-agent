from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from domain.events.base import ActorType, ContractModel, EventSource, SafetyStatus
from domain.events.registry import DomainEventPayload


class EventActor(ContractModel):
    actor_type: ActorType
    actor_id: str | None = None


class EventMetadata(ContractModel):
    node_id: str | None = None
    tool_name: str | None = None
    confidence: float | None = None
    safety_status: SafetyStatus | None = None
    trace_id: str | None = None
    request_id: str | None = None


class UserEventEnvelope(ContractModel):
    event_id: str
    event_seq: int
    user_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    occurred_at: str
    recorded_at: str
    source: EventSource
    actor: EventActor
    correlation_id: str | None = None
    causation_id: str | None = None
    idempotency_key: str | None = None
    schema_version: Literal[1] = 1
    payload: DomainEventPayload | dict[str, Any]
    metadata: EventMetadata = Field(default_factory=EventMetadata)

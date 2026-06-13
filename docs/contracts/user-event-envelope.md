---
id: VICTUS-CONTRACT-USER-EVENT-ENVELOPE
contract_id: victus.contract.events.user_event_envelope
title: User Event Envelope
status: draft
version: v1
owner: victus-agent-runtime
domain: events
contract_type: database_schema
stability: experimental
updated_at: 2026-06-12
---
# User Event Envelope

## 1. Purpose

Defines the canonical envelope for every immutable event written by the Victus Lifestyle Agent.

Domain event payloads vary by event type. The envelope does not.

## 2. Type

```ts
type UserEventEnvelope<TPayload = unknown> = {
  event_id: string
  event_seq: number
  user_id: string
  event_type: string
  aggregate_type: string
  aggregate_id: string
  occurred_at: string
  recorded_at: string
  source: "user" | "system" | "import" | "migration" | "test"
  actor: {
    actor_type: "user" | "assistant" | "system" | "tool"
    actor_id?: string
  }
  correlation_id?: string
  causation_id?: string
  idempotency_key?: string
  schema_version: 1
  payload: TPayload
  metadata: {
    node_id?: string
    tool_name?: string
    confidence?: number
    safety_status?: "ok" | "warning" | "blocked" | "needs_clarification"
    trace_id?: string
    request_id?: string
  }
}
```

## 3. Identity Rules

- `event_id` is globally unique.
- `event_seq` is assigned by the database and defines canonical ordering.
- `user_id + event_seq` defines the replay order for one user.
- `idempotency_key` prevents duplicate writes from retries.
- `aggregate_id` identifies the domain object affected by the event, such as a meal, goal, planning session, or clarification.

## 4. Event Type Naming

Use dotted lower-case event names:

```text
meal.logged
meal.edited
meal.deleted
biometrics.logged
symptom.logged
restriction.added
restriction.updated
preference.updated
goal.set
goal.adjusted
plan.session_started
plan.revision_created
plan.artifact_saved
plan.session_ended
planning.artifact_accepted
planning.artifact_rejected
feedback.recorded
feedback.resolved
clarification.requested
clarification.resolved
safety.guard_triggered
safety.action_blocked
claim.generated
evidence.cited
```

## 5. Event Store Rules

- Events are append-only.
- Events are never updated to change historical meaning.
- Corrections are represented by new events.
- Deletes are logical invalidation events, not physical removal.
- Projectors must tolerate event replay.
- Every persisted domain change must correspond to at least one event.

---
id: VICTUS-CONTRACT-EVENT-ENVELOPE-V1
title: Event Envelope V1
status: current
version: v1
updated_at: 2026-07-17
owners:
  - victus-agent-runtime
---

# Event Envelope V1

Implemented in `src/domain/events/envelope.py`.

```ts
type UserEventEnvelope<TPayload> = {
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

Identity rules:

- `event_id` is globally unique.
- `event_seq` is assigned by storage and defines canonical replay order.
- `idempotency_key` protects append retries.
- `aggregate_id` identifies the domain object affected by the event.

# Active Events

## Event Model

An event is an immutable fact produced by an accepted tool execution. It records what happened,
which user and aggregate it belongs to, when it occurred, which tool produced it, and the
action-specific payload. Events are the historical source of truth and are never edited in place.

Event envelope: `src/domain/events/envelope.py`

Active payload contracts: `src/domain/events/registry.py`

## How Events Connect the System

A tool returns an event with its execution result. `ToolRuntime` persists it through the event store
and returns a compact event reference to the agent. In the same database transaction, every
interested projector applies the event and updates its projection. Later turns load those projections
as current user context, while the original events remain available for audit and rebuilds.

Tool persistence: `src/tools/runtime.py`

Event storage: `src/victus_platform/repositories/events.py`

Projection update: `src/bootstrap/runtime.py`

## Events by Tool

### `event_capture`

Emitter: `src/tools/event_capture/actions.py`

- `meal.logged` — Records a meal and its items.

`event_capture` currently emits only `meal.logged`. Historical event contracts for other categories
remain readable by the event registry and projections, but are not accepted by this tool.

### Fullstack manual-meal import

The fullstack may deliver a manually logged meal through a dedicated authenticated ingestion
boundary. The accepted delivery becomes a `meal.logged` event with envelope source `import`; it does
not execute the conversational `event_capture` tool. Identity, grouping, idempotency, validation,
and correction rules are defined in
[Fullstack Manual Meal Import](contracts/Fullstack-Manual-Meal-Import.md).

### `profile_update`

Emitter: `src/tools/profile/actions/`

- `restriction.added` — Adds a durable user restriction.
- `preference.updated` — Records a durable user preference.

### `planning`

Emitter: `src/tools/planning/actions/`

- `goal.set` — Creates or activates a goal.
- `goal.adjusted` — Changes an existing goal.
- `plan.session_started` — Opens a planning session.
- `plan.revision_created` — Records a plan revision.
- `plan.artifact_saved` — Saves a validated planning artifact.
- `plan.session_ended` — Closes a planning session.

### `feedback`

Emitter: `src/tools/feedback/actions/`

- `feedback.recorded` — Records feedback about a specific target.
- `feedback.resolved` — Marks recorded feedback as resolved.

### `evidence_answer`

Emitter: `src/tools/evidence/actions/`

- `claim.generated` — Records a grounded claim.
- `evidence.cited` — Attaches supporting evidence to a claim.

### `clarification`

Emitter: `src/tools/interaction/clarification.py`

- `clarification.requested` — Records missing information and the question required to continue.
- `clarification.resolved` — Records the answer used to resume the workflow.

### `confirmation`

Emitter: `src/tools/interaction/confirmation.py`

- `confirmation.requested` — Records an approval request for a pending action.
- `confirmation.resolved` — Records whether the user accepted the action.

`recuperar_perfil` is read-only and emits no events.

## Event Envelope Contract

Every event uses one envelope. The payload changes by event type, while identity, ordering,
ownership, traceability, and idempotency fields remain stable.

Source: `src/domain/events/envelope.py`

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

Rules:

- `event_id` is globally unique.
- Storage assigns `event_seq`, which defines canonical replay order.
- `user_id` owns the event and `aggregate_id` identifies the affected domain object.
- `idempotency_key` prevents duplicate appends during retries.
- Events are append-only; corrections are represented by later events.
- Event payloads must use a contract registered by `src/domain/events/registry.py`.

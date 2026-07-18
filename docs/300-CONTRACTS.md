---
id: VICTUS-AGENT-CONTRACTS
title: Victus Agent Contracts
status: current
version: v1
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Victus Agent Contracts

## Contract Rule

Contracts in this repository should describe behavior that is implemented or intentionally stable.

Avoid documenting future tools, nodes, or routes as active contracts. If a future capability is
important, capture it in an ADR or issue instead of expanding this document.

## Active Runtime Contracts

Current active contracts:

- LangGraph state shape: `src/adapters/langgraph/state.py`
- tool invocation/result models: `src/tools/contracts.py`
- tool catalog: `src/tools/catalog.py`
- event models: `src/domain/events/`
- projection models: `src/domain/projections/models/`
- session context models: `src/domain/session_context/models.py`
- database schema: `src/victus_platform/database/schema.py`
- migrations: `ops/db/migrations/`
- MCP tool exposure: `src/adapters/mcp/server.py`
- MCP HTTP exposure: `src/adapters/mcp/transport.py`

Detailed reference docs remain under `docs/contracts/`.

Primary contract indexes:

- tools: `docs/contracts/tools/README.md`
- events: `docs/contracts/events/README.md`
- projections: `docs/contracts/projections/README.md`
- future tool design: `docs/contracts/future-tools/README.md`

## Source of Truth

- User history: immutable events.
- Current read state: projections rebuilt from events.
- Conversation continuity: compact session context.
- Graph execution: LangGraph state.
- Tool boundary: `ToolRuntime` returning `ToolResult` to every adapter.
- MCP transports: local stdio and deployable Streamable HTTP expose the same registered tool
  surface.

LangGraph checkpoints, LLM outputs, and response text are not canonical user history.

## Active Tool Names

The current registry exposes:

```text
event_capture
profile_update
planning
feedback
evidence_answer
clarification
confirmation
recuperar_perfil
```

Registry rules:

- safety-blocked turns expose no tools
- the runtime validates input with the catalog's Pydantic model
- all adapters receive `ToolResult`
- `event_capture` classifies/validates fast-changing user data and can emit supported
  non-safety-blocked capture events when an event store is available
- `profile_update` classifies/validates durable profile changes and can emit
  non-safety-blocked `restriction.added` and `preference.updated` events for supported actions when
  an event store is available
- `planning`, `feedback`, `evidence_answer`, `clarification`, and `confirmation` validate
  structured action input and can emit their contracted V1 events when an event store is available
- `recuperar_perfil` reads a local OAuth access token, refreshes it when possible, and performs a
  read-only backend request to `/me`
- adding or renaming a tool is a contract change

Tool-specific contracts live in `src/tools/<tool>/contract.py`. Adapter-local schemas, registries,
manifests, and action mappings are not contract sources.

## Current `ToolResult`

Implemented model:

```ts
type ToolResult = {
  status: "success" | "needs_clarification" | "blocked" | "rejected" | "error"
  data?: unknown
  events_emitted: Array<{ event_id: string; event_type: string; seq: number }>
  warnings: string[]
  clarification?: {
    missing_fields: string[]
    question: string
    expected_answer_type: string
    resume_node?: string
    resume_action?: string
  }
  safety: {
    status: "ok" | "warning" | "blocked" | "needs_clarification"
    reasons: string[]
  }
  meta: {
    confidence?: number
    schema_version: 1
    handler_version?: string
    trace_id?: string
  }
  error?: { code: string; message: string }
}
```

## Database Contract

The database is owned by this repository and migrated through Alembic under `ops/db/`.

Important guarantees:

- `user_events` is append-only user history.
- idempotency keys protect event appends.
- projections are rebuildable.
- session context is compact memory, not domain truth.
- no raw provider secrets should be stored in ordinary database fields.

See `docs/contracts/postgress-database.md` for the database diagram and index reference.

## Fundamental Contracts

Generated/synced shared contracts live under:

```text
docs/contracts/fundamental/
```

Do not edit generated fundamental contracts manually. Use:

```bash
uv run contracts sync
uv run contracts validate
```

## Compatibility Notes

The current codebase recently removed the old semantic routing implementation. References to
router embeddings, route seed files, and old tool names should not be reintroduced unless the
runtime implementation returns.

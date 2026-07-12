---
id: VICTUS-AGENT-CONTRACTS
title: Victus Agent Contracts
status: current
version: v1
updated_at: 2026-07-12
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

- LangGraph state shape: `src/agent/state.py`
- tool result model: `src/domain/tools/models.py`
- event models: `src/domain/events/models.py`
- projection models: `src/domain/projections/models.py`
- session context models: `src/domain/session_context/models.py`
- database schema: `src/infrastructure/db/schema.py`
- migrations: `ops/db/migrations/`
- MCP tool exposure: `src/victus_mcp/server.py`

Detailed reference docs remain under `docs/contracts/`.

## Source of Truth

- User history: immutable events.
- Current read state: projections rebuilt from events.
- Conversation continuity: compact session context.
- Graph execution: LangGraph state.
- Tool boundary: typed handlers returning `ToolResult`.

LangGraph checkpoints, LLM outputs, and response text are not canonical user history.

## Active Tool Names

The current registry exposes:

```text
event_capture
profile_update
```

Registry rules:

- safety-blocked turns expose no tools
- handlers validate input with Pydantic models
- handlers return `ToolResult`
- current handlers classify/validate and do not persist events
- adding or renaming a tool is a contract change

## Current `ToolResult`

Implemented model:

```ts
type ToolResult = {
  status: "success" | "needs_clarification" | "blocked" | "rejected" | "error"
  data?: unknown
  events_emitted: Array<{ event_id: string; event_type: string; event_seq: number }>
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

---
id: VICTUS-AGENT-ARCHITECTURE
title: Victus Agent Architecture
status: current
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Architectural Overview

Victus is a tool-first Python runtime. A capability has one implementation and one catalog entry;
LangGraph, MCP, CLI, and tests are access adapters around the same `ToolRuntime`.

```text
src/tools/             public capabilities, catalog, contracts, runtime
src/domain/            shared events, projections, session context, invariants
src/adapters/          LangGraph, MCP, and CLI translation
src/victus_platform/   database, repositories, LLM, safety, identity, config, telemetry
src/bootstrap/         dependency assembly
```

LangGraph owns orchestration state through checkpoints and bounded cross-thread conversational
memory through Store. Domain events and projections remain separate authoritative persistence.

# Components

## Tools

`tools/catalog.py` is the executable source of public metadata, schemas, exposure, risk, side
effects, identity requirements, and implementation references. Tool folders own their contracts,
policy, actions, and public `tool.py` entrypoint.

`tools/runtime.py` validates invocations, creates trace context, checks exposure, identity and
authorization, runs optional safety prechecks, executes the implementation, applies invocation
idempotency, persists emitted events, and returns `ToolResult`.

Clarification and confirmation live under `tools/interaction/` as continuation mechanisms.

## Domain

The domain owns immutable event contracts, rebuildable projection models/projectors, shared
session context, and small cross-capability invariants. It does not own tools or adapters.

## Adapters

- LangGraph owns conversational state, model decisions, bounded cycles, interruption, and response
  composition. Production uses PostgreSQL saver/store; tests inject in-memory implementations.
- HTTP exposes authenticated non-streaming chat and enforces thread ownership before invoke/resume.
- MCP owns discovery, authentication, transport, invocation mapping, and serialization.
- CLI owns local commands, authentication, and rendering.

Adapters never import tool actions or repositories directly for functional execution.

## Platform And Bootstrap

The platform implements technical capabilities. Bootstrap constructs repository scopes and the
shared runtime; adapters receive that configured runtime.

# Runtime Flow

```text
adapter request
  -> ToolInvocation
  -> ToolRuntime
  -> catalog lookup and contract validation
  -> identity / authorization / safety checks
  -> capability tool.py
  -> domain events
  -> event repository
  -> ToolResult
  -> adapter mapping
```

The chat graph runs `ingest -> recall -> projections -> safety -> decision -> optional interrupt ->
tool execution -> response -> memory update -> finalize`. Successful event persistence applies the
affected projection in the same database transaction before the tool reports success.

The event store remains user-history truth. Projections remain rebuildable. LangGraph state is
orchestration state only.

# Boundaries

- Tools must not import LangGraph, MCP, CLI, bootstrap, or concrete repositories.
- Adapters call only the runtime for functional tool execution.
- Platform must not contain business decisions owned by a tool.
- Catalog metadata must not be duplicated in manifests or adapter registries.

# External Dependencies

PostgreSQL persists events, projections, LangGraph checkpoints, and Store documents. MCP and the chat
API remain separate access boundaries. LiteLLM supplies model decisions and the Victus backend
validates incoming bearer identities.

# Related Documentation

- `docs/200-OPERATIONS.md`
- `docs/300-CONTRACTS.md`
- `docs/adr/20260718-tool-first-runtime.md`

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

`victus_platform` uses a qualified name because Python's standard library already owns the
top-level module name `platform`.

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

- LangGraph owns conversational state, routing, cycles, interruption, and response composition.
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

The event store remains user-history truth. Projections remain rebuildable. LangGraph state is
orchestration state only.

# Boundaries

- Tools must not import LangGraph, MCP, CLI, bootstrap, or concrete repositories.
- Adapters call only the runtime for functional tool execution.
- Platform must not contain business decisions owned by a tool.
- Catalog metadata must not be duplicated in manifests or adapter registries.

# External Dependencies

PostgreSQL persists events, projections, and session context. MCP and LangGraph provide access and
orchestration. LLM providers and the Victus web backend are reached through platform adapters.

# Related Documentation

- `docs/200-OPERATIONS.md`
- `docs/300-CONTRACTS.md`
- `docs/adr/20260718-tool-first-runtime.md`

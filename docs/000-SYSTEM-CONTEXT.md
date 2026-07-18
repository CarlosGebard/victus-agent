---
id: VICTUS-AGENT-SYSTEM-CONTEXT
title: Victus Agent System Context
status: current
updated_at: 2026-07-18
owners:
  - victus-agent-runtime
---

# Purpose

`victus-agent` is the runtime foundation for Victus lifestyle capabilities. It exposes one
implementation of each public tool through LangGraph, MCP, CLI, and tests.

# Current Scope

- Shared tool catalog, invocation/result contracts, runtime, tracing, and event persistence.
- Tools for event capture, profile, planning, feedback, evidence, and interaction continuation.
- LangGraph orchestration with normalization and safety routing.
- MCP stdio/HTTP discovery and invocation.
- Local CLI execution, auth, database operations, and validation.
- PostgreSQL events, projections, and session context.

Full coaching, semantic routing, production authorization, provider sync, and medical diagnosis
remain outside the current runtime slice.

# Core Concepts

| Concept | Meaning |
|---|---|
| Tool | Vertical product capability with one implementation. |
| Catalog | Executable source of public metadata and implementation binding. |
| ToolRuntime | Only functional execution boundary for every adapter. |
| User event | Immutable user-history fact. |
| Projection | Rebuildable read model derived from events. |
| LangGraph state | Temporary conversational orchestration state. |
| Interaction | Clarification or confirmation needed to continue execution. |

# Design Rules

- Tools never depend on LangGraph, MCP, CLI, bootstrap, or concrete repositories.
- Adapters never call internal actions or repositories for tool execution.
- Identity is adapter-resolved and runtime-checked, never inferred from free text.
- The event store is historical truth; projections and graph state are not.
- Public names remain stable and contracts are versioned.

# Documentation Map

`README.md` is the entrypoint; architecture, operations, and contracts are under `docs/`; durable
decisions live under `docs/adr/`; each capability has a local README under `src/tools/`.

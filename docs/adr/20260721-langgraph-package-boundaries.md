---
id: ADR-20260721-LANGGRAPH-PACKAGE-BOUNDARIES
title: LangGraph Adapter Package Boundaries
status: accepted
date: 2026-07-21
owners:
  - victus-agent-runtime
---

# Context

The LangGraph adapter placed orchestration, persistence support, session context, and specialized
capabilities in one flat package. The active graph remained inspectable, but module ownership and
dependency direction became harder to identify as the runtime grew.

# Decision

Organize `src/adapters/langgraph/` into three internal packages:

- `runtime/` owns persistence and conversational-runtime support.
- `engine/` owns graph state, assembly, routing, and the bounded agent loop.
- `capabilities/` owns LangGraph-specific contracts and specialized projection, safety-response,
  and translation behavior.

Keep prompt composition in the existing `prompts/` package. Preserve callable names, graph behavior,
HTTP and CLI contracts, and the canonical tool execution boundary. Update the LangGraph Studio
entrypoint to the engine graph module.

# Consequences

- Readers can distinguish orchestration from runtime integrations and specialized behavior by path.
- Internal Python import paths and documentation source references change.
- New LangGraph modules must choose one of these responsibilities rather than returning to the flat
  package.
- This reorganization does not activate legacy session-context nodes or change persistence policy.

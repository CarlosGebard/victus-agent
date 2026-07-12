---
id: VICTUS-AGENT-SYSTEM-CONTEXT
title: Victus Agent System Context
status: current
updated_at: 2026-07-12
owners:
  - victus-agent-runtime
---

# Victus Agent System Context

## Purpose

`victus-agent` is the runtime foundation for a future Victus lifestyle agent.

Today it provides a small, testable spine:

- normalize and carry a user request through a LangGraph graph
- run a safety precheck before tool exposure
- preserve compact session context
- expose typed backend tools through a static registry
- expose those tools through a local MCP stdio server
- model immutable user events and rebuildable projections
- provide local CLI and database smoke checks

It is not yet a complete nutrition planner, evidence system, mobile API, or production auth
boundary.

## Current Scope

Implemented scope:

- graph nodes: safety precheck, request normalization, context bootstrap, tool registry,
  deterministic/LLM response composition, self-harm response, session summary
- tools: `event_capture`, `profile_update`
- persistence support: event store repository, projection repository, session context repository
- operations: Alembic migrations, projection rebuild, smoke commands, MCP list/call commands

Out of current scope:

- full diet-plan generation
- plan revision workflows
- weekly review
- evidence/RAG answers
- semantic intent router
- production API and auth provider integration
- wearable/provider sync
- medical diagnosis or treatment

## Core Concepts

| Concept | Meaning |
|---|---|
| User event | Immutable fact about a user. This is the historical source of truth. |
| Projection | Rebuildable read model derived from events. |
| LangGraph state | Temporary orchestration state for a single graph run. |
| Session context | Compact conversation memory, not domain truth. |
| Tool registry | Static list of tools allowed after safety precheck. |
| Tool handler | Typed backend classifier/handler that validates input and returns `ToolResult`. |
| MCP server | Local stdio boundary exposing the same tool surface to MCP clients. |

## Design Rules

- The LLM is never the source of truth.
- Do not write directly to projections from agent nodes.
- Do not derive identity from free text.
- Do not expose mutating tools when safety blocks the turn.
- Prefer typed tool handlers over model-generated side effects.
- Keep docs tied to current code or stable contracts.

## Documentation Map

```text
README.md                  repository entrypoint
docs/000-SYSTEM-CONTEXT.md purpose, scope, concepts
docs/100-ARCHITECTURE.md   implemented runtime shape
docs/200-OPERATIONS.md     local commands and validation
docs/300-CONTRACTS.md      active contracts and compatibility notes
docs/contracts/            detailed schema/model references
docs/adr/                  decisions that still matter
docs/runbooks/             operational runbooks
```

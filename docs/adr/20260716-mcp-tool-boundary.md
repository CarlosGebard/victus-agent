---
id: ADR-20260716-MCP-TOOL-BOUNDARY
title: MCP Tool Boundary Owns Active Action Surface
status: superseded
date: 2026-07-16
owners:
  - victus-agent-runtime
---

# Context

`event_capture` and `profile_update` were implemented as graph-node-local classifiers with
duplicated schemas, validators, action metadata, event mappings, and deterministic policies under
`src/agent/nodes/*`.

That made the agent layer the implicit owner of contracts that are also exposed through the MCP
server and application tool registry.

# Decision

The active tool/action surface is the MCP-exposed application tool registry:

- public tool names remain `event_capture` and `profile_update`
- `src/victus_mcp/server.py` exposes visible registered tools over stdio
- `src/application/tools/registry.py` defines tool metadata and input schemas
- `src/application/tools/handlers.py` executes tool handlers and returns `ToolResult`
- `src/domain/tools/` owns tool input/decision models, event mappings, validation rules, action
  metadata, and deterministic policies

Graph nodes must not own duplicate tool contracts. Agent node modules may keep prompt/wrapper code,
but shared contracts and business validation belong outside `src/agent/nodes`.

# Consequences

The application tool layer no longer imports `agent.nodes`.

The graph event-capture branch consumes the application tool boundary and stores a `ToolResult`
envelope in graph state.

Codex or any other MCP client connects to the same tool surface by launching the local stdio server
with `uv run victus-mcp`.

Superseded by `20260718-tool-first-runtime.md`; MCP is now an adapter, not the owner of the tool
surface.

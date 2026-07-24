# Tool-owned domain projection reads

## Task classification

Refactor, architecture, database-read boundary, documentation, and internal contract change.

## Goal

Remove eager, graph-wide domain projection loading. A tool must load only the read models it needs
through the shared `ToolRuntime`, after the graph has selected that tool.

## Non-goals

- Do not change the `event_capture` intent or clarification behavior in this work.
- Do not change safety policy, confirmation policy, event persistence, or frontend resume handling.
- Do not add one LangGraph node per tool or duplicate projection access for chat, MCP, and CLI.
- Do not remove long-term memory recall in this work.

## Current state observations

- `load_domain_projections` always reads user profile, constraints, nutrition status, and planning
  history before `safety_precheck` and `agent_decision`.
- `agent_decision` serializes `state.projections` into its model prompt.
- The active `ToolRuntime` owns the common execution path for LangGraph, MCP, CLI, and tests, but
  currently receives only event persistence and the profile gateway.
- No current tool implementation reads a projection directly. Moving the graph node first without a
  shared replacement would remove data rather than make it tool-owned.

## Assumptions

- A tool may need read models for correct execution, but an ordinary direct response should not load
  domain projections.
- Projection reads must use the authenticated subject from `ToolContext`, never model-provided
  identity.
- The existing `projection_repository_scope` is the local persistence pattern to reuse.

## Steps

1. Inventory every canonical tool and record the minimum projection reads it actually requires.
   Keep no-read tools, including straightforward event capture, free of projection access.
2. Inventory result: no current tool implementation requires a projection read, including
   `planning`. Do not add an unused projection-reader abstraction; introduce it only with the first
   tool that has a concrete read-model dependency.
3. Remove `load_domain_projections` from `build_graph()`, its state field, prompt use in
   `agent_decision`, and debug-state rendering. Preserve the rest of the graph route unchanged.
4. Update graph-flow and graph-state documentation to remove the global projection node and describe
   tool-owned read-model access.
5. Add focused regression coverage that a direct-response turn does not execute the retired node or
   expose projections in the decision prompt.

## Validation

- Focused adapter test for no eager read or projection prompt context.
- `uv run --extra test victus test tests/test_adapters.py`
- `uv run --extra test victus check`
- One local Phoenix trace for a plain chat message, confirming the graph no longer contains
  `load_domain_projections`.

## Risks

- A future planning or profile capability may need a projection. It must add a named, minimal read
  through the shared tool runtime rather than recreating graph-wide preloading.
- A generic projection dictionary would recreate the broad-read problem inside tools.
- Existing checkpoint state can contain the retired `projections` key. The migration should ignore
  it without making it part of new turns.

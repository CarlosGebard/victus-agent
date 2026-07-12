---
id: VICTUS-AGENT-ARCHITECTURE
title: Victus Agent Architecture
status: current
updated_at: 2026-07-12
owners:
  - victus-agent-runtime
---

# Victus Agent Architecture

## Shape

The repository is organized as a small layered Python runtime:

```text
src/domain/             pure contracts and models
src/application/        config, ports, tools, MCP client, projection services
src/infrastructure/     database, repositories, provider adapters
src/agent/              LangGraph orchestration
src/victus_cli/         local CLI
src/victus_mcp/         MCP stdio server
```

The current runtime flow is:

```text
request
  -> safety_precheck
  -> normalize_request
  -> context_bootstrap
  -> self_harm_response OR tool_registry
  -> compose_response
  -> summarize_after_response
```

## Graph

The graph is built in `src/agent/graph.py`.

Current nodes:

- `safety_precheck`: allows the request by default, or calls an injected LLM client when configured.
- `normalize_request`: normalizes text and cleans legacy request fields.
- `context_bootstrap`: loads compact session summary and pending interaction state.
- `self_harm_response`: returns a blocked/support response for high-risk self-harm safety states.
- `tool_registry`: exposes visible tools when safety is not blocked.
- `compose_response`: returns either deterministic route text or an LLM-composed response.
- `summarize_after_response`: stores compact conversation summary when a repository is provided.

The graph does not currently execute tool side effects or append user events by itself.

## Tools

The active tool registry is static and lives in `src/application/tools/registry.py`.

Active tool names:

- `event_capture`
- `profile_update`

Handlers live in `src/application/tools/handlers.py`. They validate Pydantic input, run the
corresponding classifier node, and return a `ToolResult`.

Current handlers classify and validate decisions. They do not persist user events.

## MCP Boundary

`src/victus_mcp/server.py` exposes the active visible tools over stdio using the MCP package.

Local smoke commands:

```bash
uv run victus mcp-list-tools
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
uv run victus-mcp
```

## Persistence

Database support is implemented with SQLAlchemy/psycopg and Alembic.

Key modules:

- `src/infrastructure/db/engine.py`
- `src/infrastructure/db/schema.py`
- `src/infrastructure/repositories/events.py`
- `src/infrastructure/repositories/projections.py`
- `src/infrastructure/repositories/session_context.py`
- `ops/db/alembic.ini`
- `ops/db/migrations/`

Events are canonical. Projection rebuilds are application services in
`src/application/projections/runner.py`.

## LLM Boundary

Application code depends on the `LLMClient` port in `src/application/ports/llm.py`.

Provider-specific LiteLLM code lives under `src/infrastructure/llm/`.

Graph nodes may receive an `LLMClient`, but should not import provider clients directly.

## Not Implemented Yet

These concepts appear in domain models or older contracts, but are not active runtime branches:

- semantic intent router
- full diet planning
- plan revision
- weekly review
- evidence/RAG answer path
- production API/auth boundary
- end-to-end tool execution that writes events

Do not document those as active behavior until code exists.

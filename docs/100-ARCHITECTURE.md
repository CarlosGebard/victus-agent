---
id: VICTUS-AGENT-ARCHITECTURE
title: Victus Agent Architecture
status: current
updated_at: 2026-07-17
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
src/victus_mcp/         MCP stdio and HTTP servers
```

The current runtime flow is:

```text
request
  -> normalize_request
  -> safety_precheck
     -> safety_blocked_response
     -> event_capture
```

## Graph

The graph is built in `src/agent/graph.py`.

Current graph nodes:

- `normalize_request`: normalizes the request text and writes `request.working_text`.
- `safety_precheck`: writes `safety`; without an injected guard client it defaults to allow.
- `safety_blocked_response`: writes a blocked user warning and exposes no tools.
- `event_capture`: calls the application tool boundary for `event_capture` and stores the
  returned `ToolResult` envelope in graph state for allowed requests.

The graph does not currently execute tool side effects or append user events by itself.

Context bootstrap, response composition, and session summary modules still exist in the codebase,
but they are intentionally not wired into the visual graph while the first tool path is being
developed.

## Tools

The active tool registry is static and lives in `src/application/tools/registry.py`.

Active tool names:

- `event_capture`
- `profile_update`
- `recuperar_perfil`

Handlers live in `src/application/tools/handlers.py`. They validate Pydantic input, run the
corresponding domain tool policy, validate the decision, and return a `ToolResult`.

Current local classification handlers classify and validate decisions. They do not persist user
events. `recuperar_perfil` is a remote read-only tool that relays the local user token to the web
backend and does not write events.

Tool input/decision models, event mappings, validation rules, skill metadata, and deterministic
policies live under `src/domain/tools/`. Graph-node modules must not duplicate those contracts.

## MCP Boundary

`src/victus_mcp/server.py` exposes the active visible tools over stdio using the MCP package.
This is the local-user/Codex desktop transport.

`src/victus_mcp/http_server.py` exposes the same tools over Streamable HTTP at `/mcp`, with
`/health` for infrastructure checks. This is the deployable transport intended for web-app or
service-to-service LangGraph integrations.

Local smoke commands:

```bash
uv run victus mcp-list-tools
uv run victus mcp-call event_capture '{"user_id":"local-smoke-user","normalized_text":"hoy comi arroz"}'
uv run victus-mcp
uv run victus-mcp-http
```

Codex can connect to this stdio server with:

```bash
codex mcp add victus-agent -- uv run victus-mcp
```

`recuperar_perfil` reads `VICTUS_API_TOKEN` from the environment first for development override,
then reads OAuth tokens from `~/.victus/session.json`, refreshes when possible, and forwards the
access token to `GET {BACKEND_API_URL}/me`.

For deployed HTTP MCP usage, production authentication should be supplied by the calling service or
web-app boundary rather than relying on local `~/.victus/session.json` files.

LangGraph services can consume the HTTP MCP endpoint with `langchain-mcp-adapters` using a
configuration like:

```python
MultiServerMCPClient({
    "victus": {
        "transport": "http",
        "url": "http://victus-agent:8765/mcp",
    }
})
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
- multi-node graph orchestration
- context bootstrap branch in the visual graph
- response composition branch in the visual graph
- full diet planning
- plan revision
- weekly review
- evidence/RAG answer path
- production API/auth boundary
- end-to-end tool execution that writes events

Do not document those as active behavior until code exists.
